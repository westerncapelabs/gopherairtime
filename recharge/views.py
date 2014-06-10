# Create your views here.

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib import messages
from django.core.context_processors import csrf

from forms import CSVUploader


@staff_member_required
def uploader(request):
    if request.method == "POST":
        form = CSVUploader(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # mike: please check if you see the success message below.
            messages.success(request,
                "CSV has been uploaded for processing",
                    extra_tags="success")
            context = {"form": form}     
        else:
            for errors_key, error_value in form.errors.iteritems():
                messages.error(request,
                               "%s: %s" % (errors_key, error_value),
                               extra_tags="danger")
            context = {"form": form}
        context.update(csrf(request))

        return render_to_response("custom_admin/upload.html", context,
                context_instance=RequestContext(request))
    else:
        form = CSVUploader()
        context = {"form": form}
        return render_to_response("custom_admin/upload.html", context,
        context_instance=RequestContext(request))

