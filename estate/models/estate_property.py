from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero

class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Estate Property"
    _order = "id desc"
    
    # Basic fields
    name = fields.Char(string="Title", required=True)
    description = fields.Text(string="Description")
    postcode = fields.Char(string="Postcode")
    date_availability = fields.Date(
        string="Available From",
        copy=False,
        default=lambda self: fields.Date.add(fields.Date.today(), months=3),
    )
    expected_price = fields.Float(string="Expected Price", required=True)
    selling_price = fields.Float(string="Selling Price", readonly=True, copy=False)
    bedrooms = fields.Integer(string="Bedrooms", default=2)
    living_area = fields.Integer(string="Living Area (sqm)")
    facades = fields.Integer(string="Facades")
    garage = fields.Boolean(string="Garage")
    garden = fields.Boolean(string="Garden")
    garden_area = fields.Integer(string="Garden Area (sqm)")
    garden_orientation = fields.Selection(
        selection=[
            ('north', 'North'),
            ('south', 'South'),
            ('east', 'East'),
            ('west', 'West')
        ],
        string="Garden Orientation"
    )

    # Reserved/common fields
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        selection=[
            ('new', 'New'),
            ('offer_received', 'Offer Received'),
            ('offer_accepted', 'Offer Accepted'),
            ('sold', 'Sold'),
            ('cancelled', 'Cancelled'),
        ],
        string="Status",
        required=True,
        copy=False,
        default='new',
    )

    # Relations
    property_type_id = fields.Many2one(
        comodel_name="estate.property.type",
        string="Property Type",
    )

    # Parties
    salesman_id = fields.Many2one(
        comodel_name="res.users",
        string="Salesman",
        default=lambda self: self.env.user,
    )
    buyer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Buyer",
        copy=False,
    )

    tag_ids = fields.Many2many(
        comodel_name="estate.property.tag",
        string="Tags",
    )

    offer_ids = fields.One2many(
        comodel_name="estate.property.offer",
        inverse_name="property_id",
        string="Offers",
    )

    # Computed fields
    total_area = fields.Integer(
        string="Total Area (sqm)",
        compute="_compute_total_area",
        store=False,
    )
    best_price = fields.Float(
        string="Best Offer",
        compute="_compute_best_price",
        store=False,
    )

    @api.depends("living_area", "garden_area")
    def _compute_total_area(self) -> None:
        for record in self:
            living = record.living_area or 0
            garden = record.garden_area or 0
            record.total_area = living + garden

    @api.depends("offer_ids.price")
    def _compute_best_price(self) -> None:
        for record in self:
            prices = record.offer_ids.mapped("price")
            record.best_price = max(prices) if prices else 0.0

    @api.onchange("garden")
    def _onchange_garden(self) -> None:
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = "north"
        else:
            self.garden_area = 0
            self.garden_orientation = False

    # Actions
    def action_cancel(self):
        for record in self:
            if record.state == "sold":
                raise UserError("A sold property cannot be cancelled.")
            record.state = "cancelled"
        return True

    def action_set_sold(self):
        for record in self:
            if record.state == "cancelled":
                raise UserError("A cancelled property cannot be sold.")
            record.state = "sold"
        return True

    # SQL constraints
    _sql_constraints = [
        (
            "expected_price_strictly_positive",
            "CHECK(expected_price > 0)",
            "The expected price must be strictly positive.",
        ),
        (
            "selling_price_positive",
            "CHECK(selling_price >= 0)",
            "The selling price must be positive.",
        ),
    ]

    # Python-level validation for clearer errors in the UI
    @api.constrains("expected_price")
    def _check_expected_price_positive(self):
        for record in self:
            if record.expected_price is not None and record.expected_price <= 0:
                raise ValidationError("The expected price must be strictly positive.")

    @api.constrains("selling_price")
    def _check_selling_price_non_negative(self):
        for record in self:
            if record.selling_price is not None and record.selling_price < 0:
                raise ValidationError("The selling price must be positive.")

    @api.constrains("selling_price", "expected_price")
    def _check_selling_price_threshold(self):
        precision = 2
        for record in self:
            # Skip if no selling price yet
            if record.selling_price is None or float_is_zero(record.selling_price, precision_digits=precision):
                continue
            # Require a valid expected price to compare against
            if record.expected_price is None or not float_compare(record.expected_price, 0.0, precision_digits=precision) == 1:
                # expected price not set/invalid; other constraints will catch it
                continue
            min_allowed = record.expected_price * 0.9
            if float_compare(record.selling_price, min_allowed, precision_digits=precision) == -1:
                raise ValidationError("The selling price cannot be lower than 90% of the expected price.")