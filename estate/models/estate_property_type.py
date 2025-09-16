from odoo import models, fields


class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Estate Property Type"
    _order = "name"

    name = fields.Char(string="Name", required=True)
    

    _sql_constraints = [
        ("estate_property_type_name_uniq", "unique(name)", "Property type name must be unique."),
    ]
    
    # Inline list: related properties
    property_ids = fields.One2many(
        comodel_name="estate.property",
        inverse_name="property_type_id",
        string="Properties",
    )

    
