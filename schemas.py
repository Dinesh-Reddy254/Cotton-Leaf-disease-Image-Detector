# schemas.py – Marshmallow request schemas for the API

from marshmallow import Schema, fields, ValidationError

class PredictRequestSchema(Schema):
    # Expected file field – we only validate presence via custom validator
    file = fields.Raw(required=True)

    @staticmethod
    def validate_file(value):
        if not value:
            raise ValidationError("File is required")

    def load(self, data, **kwargs):
        # Custom validation to ensure 'file' present in request.files
        if 'file' not in data:
            raise ValidationError({"file": ["Missing file in request"]})
        return super().load(data, **kwargs)
