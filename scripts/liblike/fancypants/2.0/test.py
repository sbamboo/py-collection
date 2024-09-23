from fancyPants import downloadFile, fetchUrl, EventHandler, Progress, ProgressRich, ProgressTK

# Setup
handler = EventHandler()

# Fetch TEST
url = "https://github.com/sbamboo/MinecraftCustomClient/raw/refs/heads/main/v2/Repo/repo.json"

content = fetchUrl(
    url = url,
    event_handler=handler,
    progress_class=Progress,
    headers = None,
    block_size="auto",
    force_steps=None,
    yield_response=False,
    before_text=None,
    after_text=None,
    raise_for_status=True,
    progress_class_args=[],
    progress_class_kwargs={},
    requests_args=[],
    requests_kwargs={},
    text_printer=print,
    handle_gdrive_vir_warn=False,
    gdrive_vir_warn_text="Found gdrive scan warning, attempting to extract link and download from there...",
    gdrive_vir_warn_assumed_bytes=384,
    forced_encoding=None
)
#print(content)

# Download TEST
url = "https://raw.githubusercontent.com/sbamboo/MinecraftCustomClient/main/v2/Repo/Packages/1.21.1_Community-Client%20U3.B2.E/bundle.zip"

output = "test.zip"

out = downloadFile(
    url = url,
    output = output,
    stream=False,
    event_handler=handler,
    progress_class=ProgressRich,
    headers = None,
    block_size="auto",
    force_steps=None,
    before_text=None,
    after_text=None,
    raise_for_status=True,
    on_file_exist_error="remove",
    progress_class_args=[],
    progress_class_kwargs={},
    requests_args=[],
    requests_kwargs={},
    text_printer=print,
    handle_gdrive_vir_warn=False,
    gdrive_vir_warn_text="Found gdrive scan warning, attempting to extract link and download from there...",
    gdrive_vir_warn_assumed_bytes=384,
    gdrive_new_stream=None,
    forced_encoding=None
)