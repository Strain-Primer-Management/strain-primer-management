from django.contrib import admin

from .models import Plasmid, PlasmidPrimerLink

admin.site.register(Plasmid)
admin.site.register(PlasmidPrimerLink)
