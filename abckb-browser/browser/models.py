from django.db import models
from neomodel import (config, StructuredNode, StringProperty, IntegerProperty,
    UniqueIdProperty, RelationshipTo, ArrayProperty)
# Create your models here.

class Plant(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True)
    synonyms = ArrayProperty()
    source_id = StringProperty(required=True)

class Chemical(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True)
    synonyms = ArrayProperty()
    source_id = StringProperty(required=True)

class Gene(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True)
    synonyms = ArrayProperty()
    source_id = StringProperty(required=True)
    gene_type = StringProperty()
    organism = StringProperty(required=True)

class Pathway(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True)
    synonyms = ArrayProperty()
    source_id = StringProperty(required=True)

class Phenotype(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(required=True)
    synonyms = ArrayProperty()
    source_id = StringProperty(required=True)