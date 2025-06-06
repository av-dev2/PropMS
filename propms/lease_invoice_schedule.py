from __future__ import unicode_literals
import frappe
from frappe.utils import add_days, today, getdate, add_months
from propms.auto_custom import app_error_log, makeInvoiceSchedule, getDateMonthDiff
from frappe.query_builder import DocType
from pypika import functions as fn, Criterion

@frappe.whitelist()
def make_lease_invoice_schedule():
    invoice_start_date = getdate(frappe.db.get_single_value("Property Management Settings", "invoice_start_date"))
    today_date = getdate(today())

    Lease = DocType("Lease")
    query = (
        frappe.qb.from_(Lease)
        .select(Lease.name)
        .where(
            (Lease.start_date <= today_date)
            & ((Lease.end_date.isnull()) | (Lease.end_date >= today_date))
        )
    )
    lease_names = [x[0] for x in frappe.db.sql(query.get_sql())]

    for lease_name in lease_names:
        try:
            lease = frappe.get_doc("Lease", lease_name)

            lease_end = getdate(lease.end_date) if lease.end_date else add_days(today_date, 1)
            lease_start = getdate(lease.start_date) if lease.start_date else None
            if not lease_start:
                continue  # skip if no start_date

            # Clean up schedule entries for removed lease items
            lease_item_names = [li.lease_item for li in lease.lease_item]
            schedule_items = frappe.get_all("Lease Invoice Schedule", filters={"parent": lease.name}, fields=["name", "lease_item"])
            for s in schedule_items:
                if s.lease_item not in lease_item_names:
                    frappe.delete_doc("Lease Invoice Schedule", s.name)

            # Frequency map
            freq_map = {
                "Monthly": 1.0,
                "Bi-Monthly": 2.0,
                "Quarterly": 3.0,
                "6 months": 6.0,
                "Annually": 12.0,
            }

            idx = 1
            for item in lease.lease_item:
                if not item.frequency:
                    continue

                freq = freq_map.get(item.frequency)
                if not freq:
                    frappe.log_error(f"Invalid frequency '{item.frequency}' for item {item.lease_item} in lease {lease.name}", "Invalid Frequency")
                    continue

                invoice_qty = float(freq)
                invoice_date = lease_start

                # Skip invoice periods before the global invoice_start_date
                while lease_end >= invoice_date and invoice_date < invoice_start_date:
                    invoice_period_end = add_days(add_months(invoice_date, freq), -1)
                    if invoice_period_end > lease_end:
                        invoice_qty = getDateMonthDiff(invoice_date, lease_end, 1)
                    invoice_date = add_days(invoice_period_end, 1)

                # Generate invoice schedules from the valid invoice_date onward
                while lease_end >= invoice_date:
                    invoice_period_end = add_days(add_months(invoice_date, freq), -1)
                    if invoice_period_end > lease_end:
                        invoice_qty = getDateMonthDiff(invoice_date, lease_end, 1)
                    makeInvoiceSchedule(
                        invoice_date,
                        item.lease_item,
                        item.paid_by,
                        item.lease_item,
                        lease.name,
                        invoice_qty,
                        item.amount,
                        idx,
                        item.currency_code,
                        item.witholding_tax,
                        lease.days_to_invoice_in_advance,
                        item.invoice_item_group,
                        item.document_type,
                    )
                    idx += 1
                    invoice_date = add_days(invoice_period_end, 1)

            frappe.msgprint(f"Completed invoice schedule for Lease: {lease.name}")

        except Exception as e:
            frappe.msgprint(f"Error in {lease_name}. Check app error log.")
            app_error_log(frappe.session.user, f"{lease_name}: {str(e)}")
