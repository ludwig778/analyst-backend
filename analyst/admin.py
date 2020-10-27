from django.contrib import admin

from analyst.models import Asset, Index, Portfolio


class AssetAdmin(admin.ModelAdmin):
    pass


class IndexAdmin(admin.ModelAdmin):
    pass


class PortfolioAdmin(admin.ModelAdmin):
    pass


admin.site.register(Asset, AssetAdmin)
admin.site.register(Index, IndexAdmin)
admin.site.register(Portfolio, PortfolioAdmin)
