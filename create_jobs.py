'''
This job creation script operates with Mitt Romney-like efficiency to
upload the first page of each converted IPA document to Captricity.
'''
import os
import pickle
import subprocess

# You'll need to install the Captricity API client
# https://github.com/Captricity/captools
from captools.api import Client

def main():
    working_dir = os.getcwd()
    for file_name in os.listdir(working_dir):
        full_path = os.path.join(working_dir, file_name)
        if not os.path.isdir(full_path):
            continue
        full_images_path = os.path.join(full_path, 'images')
        if not os.path.isdir(full_images_path):
            print 'Skipping %s.  No images directory.' % full_path
            continue
        upload_images_to_job(full_images_path)

def upload_images_to_job(full_path):
    if not _all_pdfs_converted(full_path):
        print 'Folder %s has not finished PDF conversion, skipping!' % full_path
        return
    upload_tracker = UploadTracker(full_path)
    upload_tracker.create_captricity_job()
    upload_tracker.print_job_info()
    upload_tracker.continue_uploads()
    upload_tracker.print_finished_upload_info()

def _all_pdfs_converted(full_path):
    for pdf_file_name in os.listdir(full_path):
        if not os.path.isdir(os.path.join(full_path, pdf_file_name)):
            continue
        conversion_sigil = os.path.join(full_path, pdf_file_name, 'conversion-done')
        if not os.path.isfile(conversion_sigil):
            return False
    return True

class UploadTracker(object):
    UPLOAD_TRACKER_NAME = 'captricity-upload-status'
    JOB_ID_KEY = 'job_id'
    UPLOADED_INSTANCES_KEY = 'uploaded_instances'
    DOCUMENT_ID = '10145'
    UPLOADS_DONE_NAME = 'captricity-upload-done'
    # For messed up scans, specify the page count for sanity checks
    ODD_PDFS = {
            '/Users/nickj/IPA-data/Baringo/158_Baringo North_A.pdf':152 # Starts with an extra page 2
    }

    def __init__(self, full_path):
        self.full_path = full_path
        if os.path.isfile(self.upload_tracker_file):
            self.data = pickle.load(open(self.upload_tracker_file))
        else:
            self.data = {}
        self.data.setdefault(self.UPLOADED_INSTANCES_KEY, [])
        self.data.setdefault(self.JOB_ID_KEY, None)
        self.data.setdefault(self.UPLOADS_DONE_NAME, False)
        self.initialize_captricity_client()

    @property
    def upload_tracker_file(self):
        return os.path.join(self.full_path, self.UPLOAD_TRACKER_NAME)

    @property
    def job_id(self):
        return self.data.get(self.JOB_ID_KEY)

    @property
    def uploaded_instances(self):
        return self.data.get(self.UPLOADED_INSTANCES_KEY)

    @property
    def api_token(self):
        api_token = os.environ.get('CAPTRICITY_API_TOKEN', None)
        assert api_token is not None, "Define CAPTRICITY_API_TOKEN environment variable."
        return api_token

    @property
    def job_name(self):
        return 'IPA - ' + os.path.basename(os.path.split(self.full_path)[0])

    @property
    def job_uploading_name(self):
        return self.job_name + ' UPLOADING; NOT READY YET'

    def initialize_captricity_client(self):
        self.client = Client(self.api_token)

    def create_captricity_job(self):
        if self.job_id is not None:
            self.save()
            return
        job = self.client.create_jobs({'document_id': self.DOCUMENT_ID})
        self.data[self.JOB_ID_KEY] = job.get('id')
        self._update_job_name(self.job_uploading_name)
        self.save()

    def print_job_info(self):
        print 'Uploading %s pages to to "%s" (https://shreddr.captricity.com/admin/shreddr/job/%s/)' % (self._get_total_pdf_page_count()/2, self.job_name, self.job_id)

    def print_finished_upload_info(self):
        print '\tSanity check URLs:'
        self._get_total_pdf_page_count(sanity=True)
        uploaded_isets = self.client.read_instance_sets(self.job_id)
        print 'Finished uploading %s pages to "%s" (https://shreddr.captricity.com/admin/shreddr/job/%s/)\n' % (len(uploaded_isets), self.job_name, self.job_id)

    def _update_job_name(self, name):
        self.client.update_job(self.job_id, {'name': name})

    def continue_uploads(self):
        assert self.job_id is not None
        image_path = self._get_next_image_upload_path()
        existing_isets = { iset['name']:iset['id']
                           for iset in self.client.read_instance_sets(self.job_id) }
        while image_path is not None:
            iset_name = os.path.basename(image_path)
            if iset_name not in existing_isets:
                iset = self.client.create_instance_sets(self.job_id, {'name':iset_name})
                iset_id = iset['id']
                print '\tUploading %s to Job %s as InstanceSet %s (https://shreddr.captricity.com/admin/shreddr/instanceset/%s/)' % (image_path, self.job_id, iset_name, iset_id)
                assert len(self.client.read_instance_set_instances(iset_id)) == 0
                instance_data = {'page_number':'0', 'image_file':open(image_path, 'rb')}
                self.client.create_instance_set_instances(iset_id, instance_data)
            else:
                iset_id = existing_isets[iset_name]
            assert len(self.client.read_instance_set_instances(iset_id)) == 1, 'Problem with InstanceSet %s' % iset_id
            self.uploaded_instances.append(image_path)
            self.save()
            image_path = self._get_next_image_upload_path()
        self._sanity_check()
        self._update_job_name(self.job_name)
        self.data[self.UPLOADS_DONE_NAME] = True
        self.save()

    def _sanity_check(self):
        image_paths = self._get_all_image_full_paths()
        uploaded_isets = self.client.read_instance_sets(self.job_id)
        total_pages = self._get_total_pdf_page_count()
        assert total_pages/2.0 == len(uploaded_isets), 'Unexpected page counts: %s vs %s' % (total_pages/2.0, len(uploaded_isets))
        uploaded_iset_names = [iset['name'] for iset in uploaded_isets]
        expected_iset_names = [os.path.basename(image_path) for image_path in image_paths]
        uploaded_iset_name_set = set(uploaded_iset_names)
        expected_iset_name_set = set(expected_iset_names)
        assert len(uploaded_iset_names) == len(uploaded_iset_name_set), 'Not all uploaded iset names were unique!'
        assert len(expected_iset_names) == len(expected_iset_name_set), 'Not all expected iset names were unique!'
        assert len(uploaded_iset_names) == len(expected_iset_names), 'Different numbers of uploaded and expected isets: %s vs %s' % (len(uploaded_iset_names), len(expected_iset_names))
        difference = expected_iset_name_set - uploaded_iset_name_set
        assert len(difference) == 0, 'Difference: %s' % difference
        difference = uploaded_iset_name_set - expected_iset_name_set
        assert len(difference) == 0, 'Difference: %s' % difference

    def _get_total_pdf_page_count(self, sanity=False):
        pdf_dir = os.path.split(self.full_path)[0]
        total_count = 0
        for file_name in os.listdir(pdf_dir):
            if not file_name.endswith('.pdf'):
                continue
            pdf_file_path = os.path.join(pdf_dir, file_name)
            page_count = self._get_pdf_file_page_count(pdf_file_path)
            if sanity:
                print '\t\t%s: %s pages.  https://shreddr.captricity.com/admin/shreddr/instance/?instance_set__job__id__exact=%s&p=%s' % (pdf_file_path, page_count, self.job_id, total_count/10)
            total_count += page_count
        return total_count

    def _get_pdf_file_page_count(self, pdf_file_path):
        pdfinfo_output = subprocess.check_output(['pdfinfo', pdf_file_path])
        num_pages = None
        for tok in pdfinfo_output.split('\n'):
            if tok.find('Pages') < 0: continue
            num_pages_str = tok[tok.find(':')+1:].strip() # it should always reach here
            if num_pages_str.isdigit():
                num_pages = int(num_pages_str)
                break
        assert num_pages is not None
        if num_pages % 2 != 0:
            num_pages = self.ODD_PDFS[pdf_file_path]
        return num_pages

    def _get_next_image_upload_path(self):
        all_image_paths = self._get_all_image_full_paths()
        for image_path in all_image_paths:
            if image_path not in self.uploaded_instances:
                return image_path
        return None

    def _get_all_image_full_paths(self):
        all_images = []
        for pdf_file_name in os.listdir(self.full_path):
            pdf_images_path = os.path.join(self.full_path, pdf_file_name)
            if not os.path.isdir(pdf_images_path):
                continue
            all_images.extend(self._get_pdf_image_full_paths(pdf_images_path))
        return all_images

    def _get_pdf_image_full_paths(self, pdf_images_path):
        # We assume the bigger files are the page we want
        even_dir = os.path.join(pdf_images_path, 'even-pages')
        odd_dir = os.path.join(pdf_images_path, 'odd-pages')
        assert os.path.isdir(even_dir), 'Not a directory: %s' % even_dir
        assert os.path.isdir(odd_dir), 'Not a directory: %s' % odd_dir
        even_files = os.listdir(even_dir)
        odd_files = os.listdir(odd_dir)
        even_files = [os.path.join(pdf_images_path, 'even-pages', f) for f in even_files]
        odd_files = [os.path.join(pdf_images_path, 'odd-pages', f) for f in odd_files]
        if len(odd_files) == 0 or len(even_files) == 0:
            return []
        even_file_sizes = [os.path.getsize(f) for f in even_files]
        odd_file_sizes = [os.path.getsize(f) for f in odd_files]
        FUDGE_FACTOR = 50000 # expect 50kb avg difference, otherwise raise error
        avg_even_size = float(sum(even_file_sizes))/len(even_file_sizes)
        avg_odd_size = float(sum(odd_file_sizes))/len(odd_file_sizes)
        if avg_even_size - FUDGE_FACTOR > avg_odd_size:
            return even_files
        elif avg_odd_size - FUDGE_FACTOR > avg_even_size:
            return odd_files
        raise Exception('Could not distinguish files: %s' % pdf_images_path)

    def save(self):
        fout = open(self.upload_tracker_file, 'w')
        pickle.dump(self.data, fout)
        fout.close()

if __name__ == "__main__":
    main()
