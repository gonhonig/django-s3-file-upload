# django-s3-file-upload
app for uploading multiple heavy files from django admin to AWS S3 directly from the client using jQuery AJAX

## Installation
Use the package manager pip to install django-s3-file-upload.
```bash
pip install git+git://github.com/gonhonig/django-s3-file-upload.git
```

## Requeriments
- ``django``
- ``boto3``

## Usage
1. Set up your AWS S3 credentials in settings.py as following:
	```python
	AWS_STORAGE_BUCKET_NAME = <your-bucket-name>
	AWS_S3_REGION_NAME = <your-region-name>
	AWS_ACCESS_KEY_ID = <your-access-key>
	AWS_SECRET_ACCESS_KEY = <your-secret-key>
	``` 
2. Add ``'fileupload'`` to your ``INSTALLED_APPS``
3. Inherit Your ModelAdmin from ``fileupload.admin.FileuploadAdmin``
	Your ModelAdmin can either have a FileField itself, or it has anothe Model with FileField related to it using a ForeignKey field.
	```python
	from fileupload import FileuploadAdmin

	class MyModelAdmin(FileuploadAdmin):
	    # those values set by default:
	    change_form_template = 'fileupload/change_form.html'
	    change_list_template = 'fileupload/change_list.html'
	    multiupload_template = 'fileupload/upload.html'
	    #if True enable file upload on item edit screen. False by default.
	    fileupload_form = True
	    #if True enable file upload on list screen. False by default.
	    fileupload_list = True
	    #the Model related to the ModelAdmin by FK, which has the FileField for upload. default is the ModelAdmin's Model.
	    file_model = models.RelatedModelWithFileField
	    #file_model's fields to include in the ModelForm. empty by default
	    upload_options = ['folder', 'bid']
	    #image compression options to feed Compressor.js module. added 'fit' functionality (cover or strech)
	    image_compressor = {'width': 1000, 'height': 800, 'quality': 0.8, 'fit': 'cover'}
	    #if True, adds a Content-Disposition: attachment header to the uploaded file. False by default.
	    attachment = True
	```