# Use our GEO Uploader to submit data to GEO

The following steps explain how to create a GEO account and subsequently use that account to upload sequencing data using our uploader.

## Step-by-Step Guide

### 1) Create Your Personal Space with GEO

- Visit [NCBI GEO](https://www.ncbi.nlm.nih.gov/geo/)
- Sign up or log in to your account
- This will be the person that will be shown as owner of the data at GEO

### 2) Navigate to the GEO Submissions page

Make sure you're logged in: https://account.ncbi.nlm.nih.gov/?back_url=https://www.ncbi.nlm.nih.gov/geo/submitter/

Navigate to the submission page: https://www.ncbi.nlm.nih.gov/geo/info/submissionftp.html

**To manually find the submissions page starting from your profile (if you didn't log in):**
- Log in to GEO and you will find yourself at your GEO Profile
- Click on the bottom right button: **New Submission**
- ![new_submission](/images/new_submission.png)
- Click on the first link shown under Data Types: **Submit high-throughput sequencing (HTS)**
- ![HTS](/images/HTS.png)
- Towards the bottom of the page, under "Uploading your submission" click on **Transfer files**
- ![transfer_files](/images/transfer_files.png)

### 3) Save Your Credentials

- **Save your personalized upload space:** This is typically shown as `uploads/YOUR@EMAIL_i1Y9oymE` or `upload/<YOUR LOGIN>_<some random string>` at the top of the page
- ![upload_folder](/images/upload_folder.png)
- **Save your upload space password:** You'll find this under Step 2, Point F on the submission page
- ![remote password](/images/remote_password.png)

### 4) Log in to the GEO Uploader

- Launch the server from the terminal `conda run -n gi_geo-uploader flask start-prod`
- Access the uploader by visiting http://127.0.0.1:8000 (or whatever your selected port is)

### 5) Create a New Session

- Enter the paths to your raw and processed datasets from our server

### 6) Submit Your Data

- Enter a title for your submission
- Select relevant samples from the list provided, using the filter functionality if needed

### 7) Complete Metadata

- On the dashboard, click the **Complete Metadata** button
- Fill in the required information for each tab: Study, Samples, and Protocol

### 8) Wait for upload to be finished

- Wait for the **Gathering Process** job to complete (View Gather Process Button)
- Wait for the **Upload Process** job to complete (View Upload Process Button)

### 9) Upload your metadata

- Once ready, click on the **"Download metadata"** button to download the metadata. It's a single Excel file with multiple sheets
- Login to GEO: https://account.ncbi.nlm.nih.gov/?back_url=https://www.ncbi.nlm.nih.gov/geo/submitter/
- In GEO navigate to: https://submit.ncbi.nlm.nih.gov/geo/submission/meta/

---

## Important Links

- **NCBI GEO:** https://www.ncbi.nlm.nih.gov/geo/
- **GEO Login:** https://account.ncbi.nlm.nih.gov/?back_url=https://www.ncbi.nlm.nih.gov/geo/submitter/
- **GEO Submission FTP Info:** https://www.ncbi.nlm.nih.gov/geo/info/submissionftp.html
- **GEO Metadata Submission:** https://submit.ncbi.nlm.nih.gov/geo/submission/meta/