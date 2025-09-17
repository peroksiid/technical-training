from odoo import models, Command
from odoo.exceptions import UserError


class EstateProperty(models.Model):
    _inherit = "estate.property"

    def action_set_sold(self):
        # Step 2: create an empty customer invoice for the buyer
        for prop in self:
            buyer = prop.buyer_id
            if not buyer:
                # If no buyer is set we can't invoice; skip gracefully
                continue
            Move = self.env["account.move"].with_context(default_move_type="out_invoice")
            journal = Move._get_default_journal()
            if not journal:
                # Surface a clear error if no sales journal is set up
                raise UserError("No Sales Journal configured for this company.")
            fee_percent = (prop.selling_price or 0.0) * 0.06
            admin_fee = 100.0
            Move.create({
                "partner_id": buyer.id,
                "move_type": "out_invoice",
                "journal_id": journal.id,
                "invoice_line_ids": [
                    Command.create({
                        "name": "6% Commission on selling price",
                        "quantity": 1,
                        "price_unit": fee_percent,
                    }),
                    Command.create({
                        "name": "Administrative fees",
                        "quantity": 1,
                        "price_unit": admin_fee,
                    }),
                ],
            })
        return super().action_set_sold()


