from __future__ import unicode_literals
import frappe
from frappe.utils import add_days, today, getdate, add_months
from propms.auto_custom import app_error_log, makeInvoiceSchedule, getDateMonthDiff
from frappe.query_builder import DocType

@frappe.whitelist()
def make_lease_invoice_schedule():
    settings = frappe.get_single("Property Management Settings")
    if not settings.get("make_invoice_schedule_up_to_tomorrow_only", 0):
        return
    invoice_start_date = getdate(settings.get("invoice_start_date", None))

    use_valid_from_date = settings.use_valid_from_date
    today_date = getdate(today())
    next_month_end = add_days(add_months(today_date, 1), -1)

    Lease = DocType("Lease")
    query = (
        frappe.qb.from_(Lease)
        .select(Lease.name)
        .where(Lease.start_date <= today_date)
    )
    lease_names = [row[0] for row in frappe.db.sql(query.get_sql())]

    freq_map = {
        "Monthly": 1.0,
        "Bi-Monthly": 2.0,
        "Quarterly": 3.0,
        "6 months": 6.0,
        "Annually": 12.0,
    }

    for lease_name in lease_names:
        try:
            lease = frappe.get_doc("Lease", lease_name)
            schedule_end = getdate(lease.end_date) if lease.end_date else next_month_end
            schedule_start = invoice_start_date if invoice_start_date > lease.start_date else lease.start_date
            if not schedule_start:
                continue

            lease_item_names = [li.lease_item for li in lease.lease_item]
            schedule_items = frappe.get_all("Lease Invoice Schedule", filters={"parent": lease.name}, fields=["name", "lease_item"])
            for s in schedule_items:
                if s.lease_item not in lease_item_names:
                    frappe.delete_doc("Lease Invoice Schedule", s.name)

            idx = 1
            for item in lease.lease_item:
                if not item.frequency:
                    continue
                freq = freq_map.get(item.frequency)
                if not freq:
                    frappe.log_error(f"Invalid frequency '{item.frequency}' for item {item.lease_item} in lease {lease.name}", "Invalid Frequency")
                    continue

                invoice_qty = float(freq)
                item_amount = item.amount

                lease_items = frappe.get_all(
                    "Lease Item",
                    filters={
                        "parent": lease.name,
                        "lease_item": item.lease_item,
                        "valid_from": ("<=", today_date)
                    },
                    fields=["amount", "valid_from"],
                    order_by="valid_from desc",
                    limit=1
                )
                if use_valid_from_date and lease_items:
                    item_amount = lease_items[0].amount

                invoice_date = schedule_start
                while schedule_end >= invoice_date and invoice_date <= next_month_end:
                    invoice_period_end = add_days(add_months(invoice_date, freq), -1)

                    if schedule_start <= invoice_date <= next_month_end:
                        exists = frappe.db.exists(
                            "Lease Invoice Schedule",
                            {
                                "parent": lease.name,
                                "lease_item": item.lease_item,
                                "date_to_invoice": invoice_date,
                            }
                        )
                        if not exists:
                            makeInvoiceSchedule(
                                invoice_date,
                                item.lease_item,
                                item.paid_by,
                                item.lease_item,
                                lease.name,
                                invoice_qty,
                                item_amount,
                                idx,
                                item.currency_code,
                                item.witholding_tax,
                                lease.days_to_invoice_in_advance,
                                item.invoice_item_group,
                                item.document_type,
                            )
                            frappe.db.commit()
                            idx += 1

                    invoice_date = add_days(invoice_period_end, 1)

            frappe.msgprint(f"Completed invoice schedule for Lease: {lease.name}")

        except Exception as e:
            frappe.msgprint(f"Error in {lease_name}. Check app error log.")
            app_error_log(frappe.session.user, f"{lease_name}: {str(e)}")
