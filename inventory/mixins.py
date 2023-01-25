import io
import csv
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponse
from .forms import UploadCSVForm
from .utils import pluralize


class WriteCSVMixin(object):
    def write_csv(self, filename):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return {"writer": csv.writer(response), "response": response}


class ReadCSVMixin(object):
    def read_csv(self, request):
        form = UploadCSVForm(request.POST, request.FILES)

        if form.is_valid():
            csv_file = request.FILES["csv"]

            if not csv_file.name.endswith(".csv"):
                messages.error(request, "Please choose a CSV file.")
                return False

            data_set = csv_file.read().decode("UTF-8")
            io_string = io.StringIO(data_set)

            return csv.DictReader(io_string, delimiter=",", quotechar='"')
        else:
            messages.error(request, "Nope.")
            return False


class RedirectAfterImportMixin(object):
    def redirect(self, request, count, item):
        noun = item["noun"]
        try:
            url = item["redirect_url"]
        except KeyError:
            url = "settings"

        if count:
            messages.success(request, f"Imported {count} {pluralize(noun, count)}.")
        else:
            messages.info(request, f"No {noun}s imported.")

        return redirect(reverse(url))
