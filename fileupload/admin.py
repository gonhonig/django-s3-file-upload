import os
from django.contrib import admin
from django.forms import modelform_factory
from django.shortcuts import render
from django.urls import path, reverse
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.core.files.base import ContentFile
from .utils import s3_upload_creds


class FileuploadAdmin(admin.ModelAdmin):
    change_form_template = 'fileupload/change_form.html'
    change_list_template = 'fileupload/change_list.html'
    fileupload_template = 'fileupload/upload.html'
    fileupload_form = False
    fileupload_list = False
    upload_options = None
    file_model = None
    file_field_name = 'file'
    image_compressor = False
    attachment = False

    def __init__(self, model, admin_site):
        if self.file_model == None:
            self.file_model = model
        super().__init__(model, admin_site)

    def get_model_name(self):
        options = self.model._meta
        if hasattr(options, 'model_name'):
            return getattr(options, 'model_name')
        return getattr(options, 'module_name')


    def get_fileupload_form_view_name(self):
        app_name = self.model._meta.app_label
        return '%s_%s_fileupload_form' % (app_name, self.get_model_name())


    def get_fileupload_list_view_name(self):
        app_name = self.model._meta.app_label
        return '%s_%s_fileupload_list' % (app_name, self.get_model_name())


    def get_api_files_policy_view_name(self):
        app_name = self.model._meta.app_label
        return '%s_%s_api_files_policy' % (app_name, self.get_model_name())


    def render_change_form(self, request, context, *args, **kwargs):
        context.update({
            'fileupload_form': self.fileupload_form,
        })
        if self.fileupload_form:
            if 'object_id' in context:
                object_id = context['object_id']
                if object_id is not None:
                    context.update({
                        'fileupload_form_url': reverse(
                            'admin:%s' % self.get_fileupload_form_view_name(),
                            args=[object_id, ]),
                        })
        return super(FileuploadAdmin, self).render_change_form(request, context, *args, **kwargs)


    def changelist_view(self, request, extra_context=None):
        pop = request.POST.get('pop')
        extra_context = extra_context or {}
        extra_context.update({
            'fileupload_list': self.fileupload_list,
        })
        if self.fileupload_list:
            url = reverse('admin:%s' % self.get_fileupload_list_view_name())
            if pop:
                url += '?pop=1'
            extra_context.update({
                'fileupload_list_url': url,
            })
        return super(FileuploadAdmin, self).changelist_view(request, extra_context)


    def get_urls(self, *args, **kwargs):
        urls = super().get_urls()
        extra_urls = []
        if self.fileupload_form:
            extra_urls += [
            	path('<int:parent_id>/upload/', 
                    self.admin_site.admin_view(self.upload_view), 
                    name=self.get_fileupload_form_view_name()
                    ),
            	path('<int:parent_id>/api-files-policy/',
                    self.admin_site.admin_view(self.api_view), 
                    name=self.get_api_files_policy_view_name())
            ]
        if self.fileupload_list:
            extra_urls += [
                path('upload/', 
                    self.admin_site.admin_view(self.upload_view), 
                    name=self.get_fileupload_list_view_name()
                    ),
                path('api-files-policy/',
                    self.admin_site.admin_view(self.api_view), 
                    name=self.get_api_files_policy_view_name())
            ]
        return extra_urls + urls


    def get_model_form(self, parent=None):
        fields = self.upload_options
        if parent and parent in fields:
            fields.remove(parent)
        return modelform_factory(self.file_model, fields=fields)


    def upload_view(self, request, parent_id=None):
        if parent_id:
            parent = self.get_object(request, parent_id)
            parent_field_name = [field.name for field in parent._meta._relation_tree if field.model == self.file_model][0]
            api_template_args = [parent_id]
        else:
            parent = None
            api_template_args = []
            parent_field_name = None

        form = None
        if self.upload_options:
            form = self.get_model_form(parent_field_name)

        context = {
            "object": parent,
            'media': self.media,
            'opts': self.model._meta,
            'change': False,
            'is_popup': 'pop' in request.GET,
            'add': True,
            'app_label': self.model._meta.app_label,
            'has_permission': True,
            'has_delete_permission': False,
            'has_add_permission': False,
            'has_change_permission': False,
            'api_files_policy_url': reverse('admin:%s' % self.get_api_files_policy_view_name(), args=api_template_args),
            'form': form,
            'image_compressor': self.image_compressor,
            'attachment': self.attachment,
            }

        return render(request, self.fileupload_template, context)


    def api_view(self, request, parent_id=None):
        if parent_id:
            parent = self.get_object(request, parent_id)
            parent_field_name = [field.name for field in parent._meta._relation_tree if field.model == self.file_model][0]
        else:
            parent = None
            parent_field_name = None

        if request.method == 'POST':
            """
            save the object
            """
            options = {}
            form = self.get_model_form(parent_field_name)(request.POST)
            if form.is_valid():
                for key in request.POST.keys():
                    if not key in ['filename', 'csrfmiddlewaretoken']:
                        options[key] = form.cleaned_data[key]
            dummy_file = ContentFile('')
            dummy_file.name = request.POST['filename']
            options[self.file_field_name] = dummy_file
            if parent:
                options[parent_field_name] = parent
            file_obj = self.file_model.objects.create(**options)

            """
            get s3 credentials
            """
            file_obj_id = file_obj.id
            media_url = settings.MEDIA_URL.split('/')[-2]
            file_upload_path = '{0}/{1}'.format(media_url, file_obj.file.name)
            file_name, file_extension = os.path.splitext(file_upload_path)
            file_name = file_name.split('/')[1]            
            cerds = s3_upload_creds(file_upload_path, self.attachment)

            return JsonResponse(cerds)
