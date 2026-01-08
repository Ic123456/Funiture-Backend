from django.apps import AppConfig


class FunitureConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'funiture'
    
        
    def ready(self):
        # import signals so receivers are registered
        import funiture.signals
