from odoo import models, fields, api
from datetime import date, timedelta


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Estate Property Offer"

    price = fields.Float(string="Price")
    status = fields.Selection(
        selection=[("accepted", "Accepted"), ("refused", "Refused")],
        string="Status",
        copy=False,
    )
    partner_id = fields.Many2one("res.partner", string="Partner", required=True)
    property_id = fields.Many2one("estate.property", string="Property", required=True)

    validity = fields.Integer(string="Validity (days)", default=7)
    date_deadline = fields.Date(string="Deadline", compute="_compute_date_deadline", inverse="_inverse_date_deadline", store=False)

    @api.depends("validity", "create_date")
    def _compute_date_deadline(self) -> None:
        for offer in self:
            created = (offer.create_date or fields.Datetime.now())
            base_date = created.date() if hasattr(created, "date") else date.today()
            offer.date_deadline = base_date + timedelta(days=offer.validity or 0)

    def _inverse_date_deadline(self) -> None:
        for offer in self:
            created = (offer.create_date or fields.Datetime.now())
            base_date = created.date() if hasattr(created, "date") else date.today()
            if offer.date_deadline:
                delta = offer.date_deadline - base_date
                offer.validity = max(delta.days, 0)
