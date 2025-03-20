from django.core.management.base import BaseCommand
from inventory.models import Profile


class Command(BaseCommand):
    help = "Set the color preference for a user"

    def add_arguments(self, parser):
        parser.add_argument(
            "--theme",
            type=str,
            choices=["light", "dark", "auto"],
            default="auto",
            help="Set the color preference theme (light, dark, or auto)",
        )
        parser.add_argument(
            "--user",
            type=str,
            required=True,
            help="Specify the username of the user to set the color preference for",
        )

    def handle(self, *args, **kwargs):
        theme = kwargs["theme"]
        username = kwargs["user"]
        try:
            profile = Profile.objects.get(user__username=username)
            profile.color_preference = theme
            profile.save()
            self.stdout.write(
                self.style.SUCCESS(f"Color preference set to '{theme}' for {username}")
            )
        except Profile.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"User with username '{username}' does not exist")
            )
