# FancyPants/BeautifulPants 2.0 Preview by Simon Kalmi Claesson
# Python library to download files or fetch get requests, with the possibility of a progress bar.
#

import os
import requests
from bs4 import BeautifulSoup
from rich.progress import Progress as RichProgress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, DownloadColumn, RenderableColumn, TimeRemainingColumn, TransferSpeedColumn

def convert_bytes(bytes_size, binary_units=False):
    """Converts bytes to the highest prefix (B, kB, MB, GB, TB, PB or GiB, MiB, etc.)."""
    if binary_units:
        prefixes = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']
        base = 1024
    else:
        prefixes = ['B', 'kB', 'MB', 'GB', 'TB', 'PB']
        base = 1000

    size = float(bytes_size)
    index = 0

    while size >= base and index < len(prefixes) - 1:
        size /= base
        index += 1

    return f"{size:.2f} {prefixes[index]}"


def get_optimal_block_size(file_size):
    """Determines an optimal block size based on file size."""
    if file_size < 1 * 1024 * 1024:  # < 1 MB
        return 8 * 1024  # 8 KB
    elif file_size < 100 * 1024 * 1024:  # < 100 MB
        return 64 * 1024  # 64 KB
    elif file_size < 1 * 1024 * 1024 * 1024:  # < 1 GB
        return 512 * 1024  # 512 KB
    elif file_size < 5 * 1024 * 1024 * 1024:  # < 5 GB
        return 1 * 1024 * 1024  # 1 MB
    
    #elif file_size < 10 * 1024 * 1024 * 1024:  # < 10 GB
    #    return 4 * 1024 * 1024  # 4 MB
    #elif file_size < 20 * 1024 * 1024 * 1024:  # < 20 GB
    #    return 8 * 1024 * 1024  # 8 MB
    #else:
    #    return 16 * 1024 * 1024  # 16 MB for very large files
    
    else:
        return 1 * 1024 * 1024  # 1 MB

def gdrive_vir_warn_url_extractor(HTMLsource):
    # attempt extract
    soup = BeautifulSoup(HTMLsource, 'html.parser')
    form = soup.find('form')
    linkBuild = form['action']
    hasParams = False
    inputs = form.find_all('input')
    toBeFound = ["id","export","confirm","uuid"]
    for inp in inputs:
        name = inp.attrs.get('name')
        value = inp.attrs.get('value')
        if name != None and name in toBeFound and value != None:
            if hasParams == False:
                pref = "?"
                hasParams = True
            else:
                pref = "&"
            linkBuild += f"{pref}{name}={value}"
    return linkBuild

class EventCancelSenser(Exception):
    def __init__(self, message):
        super().__init__(message)

class EventHandler:
    def __init__(self):
        self.children = {}
        self.event_id_counter = 0

    def _get_new_event_id(self):
        """Generates and returns a new unique event ID."""
        self.event_id_counter += 1
        return self.event_id_counter

    def create_generic(self, receiver, *args, **kwargs):
        """Creates a generic event receiver object and returns its event ID."""
        event_id = self._get_new_event_id()
        self.children[event_id] = receiver(self, *args, **kwargs)
        if not isinstance(self.children[event_id],EventReciever):
            raise TypeError("Newly created reciever was not of type and/or in inhertance of the 'EventReciever' object!")
        return event_id

    def get_reciever(self,event):
        return self.children[event]

    def update_progress(self, event, current_steps):
        """Updates the progress of a given event."""
        if event in self.children:
            self.children[event].update(current_steps)
    
    def update_params(self, event, **kwargs):
        """Updates the parameters of a given event."""
        if event in self.children:
            self.children[event].update_params(**kwargs)

    def reset_progress(self, event):
        """Resets the progress of a given event."""
        if event in self.children:
            self.children[event].reset()

    def end(self, event, successful=True):
        """Ends the progress of a given event and removes it from the handler."""
        if event in self.children:
            self.children[event].end(successful)
            del self.children[event]

class EventReciever:
    def __init__(self,parent):
        self.canceled = False
        if parent:
            self.parent = parent
        else:
            raise Exception("Parent must be sent when initing an EventReciever!")

    def update(self,current):
        raise NotImplementedError()

    def update_params(self,**kwargs):
        for k,v in kwargs.items():
            setattr(self,k,v)

    def reset(self):
        raise NotImplementedError()

    def end(self,successful):
        raise NotImplementedError()

class Progress(EventReciever):
    """Basic progress handler that prints '<current>/<total>'."""
    def __init__(self, parent, total_steps, block_size, conv_bytes=True, *un_used_a, **un_used_kw):
        super().__init__(parent)
        self.total_steps = total_steps
        self.current_steps = 0
        self.block_size = block_size
        self.conv_bytes = conv_bytes

    def update(self, current_steps):
        """Updates the progress and prints it."""
        self.current_steps = current_steps
        self.print_progress()

    def reset(self):
        self.current_steps = 0
        self.print_progress()

    def print_progress(self):
        """Prints the current progress in the format 'current/total'."""
        cur = self.current_steps
        tot = self.total_steps
        if self.conv_bytes == True:
            cur = convert_bytes(cur)
            tot = convert_bytes(tot)
        print(f'{cur}/{tot} (Block size: {convert_bytes(self.block_size)})')

    def end(self, successful):
        """Prints the status of the progress event as ended."""
        status = "Success" if successful else "Failed"
        print(f'Progress ended with status: {status}')

class ProgressRich(EventReciever):
    """Rich progress handler that uses a visual progress bar."""
    def __init__(self, parent, total_steps, block_size, title="Downloading...", conv_bytes=True, show_block_size=False, expand_task=False):
        super().__init__(parent)
        self.total_steps = total_steps
        self.current_steps = 0
        self.block_size = block_size  # Store block_size
        self.expand_task = expand_task
        self.title = title
        self.show_block_size = show_block_size

        # Include block size in the title if specified
        block_size_str = f" (bz: {convert_bytes(block_size)})" if show_block_size else ""
        self.progress = RichProgress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            DownloadColumn() if conv_bytes == True else RenderableColumn(""),
            RenderableColumn("[cyan]ETA:"),
            TimeRemainingColumn(compact=True),
            TransferSpeedColumn(),
        )
        self.task = self.progress.add_task(title + block_size_str, total=total_steps)
        self.progress.start()  # Start the rich progress bar

    def update(self, current_steps):
        """Updates the rich progress bar."""
        self.current_steps = current_steps
        self.progress.update(self.task, completed=current_steps, expand=self.expand_task)

    def reset(self):
        self.current_steps = 0
        block_size_str = f" (bz: {convert_bytes(self.block_size)})" if self.show_block_size else ""
        self.progress.reset(self.task, expand=self.expand_task, total=self.total_steps, description=self.title+block_size_str)

    def end(self, successful):
        """Stops the rich progress bar and prints status."""
        self.progress.stop()  # Stop the rich progress bar

class ProgressTK(EventReciever):
    """Tkinter progress handler that displays a progress bar in a window."""
    def __init__(self, parent, total_steps, block_size, title="Download Progress", conv_bytes=True, onreset_text="Download reset. Ready to start again."):
        super().__init__(parent)

        import tkinter as tk
        from tkinter import ttk

        self.total_steps = total_steps
        self.current_steps = 0
        self.block_size = block_size
        self.conv_bytes = conv_bytes
        self.onreset_text = onreset_text

        # Create Tkinter window
        self.window = tk.Tk()
        self.window.title(title)
        
        # Create progress bar
        self.progress_bar = ttk.Progressbar(self.window, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.pack(pady=20)
        
        self.label = tk.Label(self.window, text="Starting download...")
        self.label.pack(pady=10)
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)  # Handle window close
        self.window.geometry("400x100")
        
        self.window.update()

    def update(self, current_steps):
        """Updates the Tkinter progress bar."""
        if self.canceled == False:
            self.current_steps = current_steps
            self.progress_bar['value'] = (self.current_steps / self.total_steps) * 100
            cur = self.current_steps
            tot = self.total_steps
            if self.conv_bytes == True:
                cur = convert_bytes(cur)
                tot = convert_bytes(tot)
            self.label.config(text=f'Downloading: {cur}/{tot} ({(self.current_steps / self.total_steps) * 100:.2f}%) (Block size: {convert_bytes(self.block_size)})')
            self.window.update()

    def end(self, successful):
        """Closes the Tkinter window and prints status."""
        if self.canceled == False:
            self.window.destroy()  # Close the Tkinter window

    def on_close(self):
        """Handles window close event."""
        self.canceled = True # Tell ProgressTK and the downloader that this eventReciever is canceled
        self.window.destroy()  # Close the window

    def reset(self):
        """Resets the progress bar and current steps."""
        self.current_steps = 0
        self.progress_bar['value'] = 0
        self.label.config(text=self.onreset_text)
        self.window.update()


def downloadFile(url,output,stream=False, event_handler=EventHandler,progress_class=Progress, block_size="auto", force_steps=None, before_text=None,after_text=None, raise_for_status=True,on_file_exist_error="raise", progress_class_args=[], progress_class_kwargs={}, requests_args=[], requests_kwargs={}, text_printer=print, handle_gdrive_vir_warn=False,gdrive_vir_warn_text="Found gdrive scan warning, attempting to extract link and download from there...",gdrive_vir_warn_assumed_bytes=384,gdrive_new_stream=None, forced_encoding=None, _ovvEventId=None):
    """
    Function over requests.get that uses an EventHandler to allow for UI/TUI visual-progress of a file download.
    To just wrap requests.get and fetch content use `fetchUrl`.

    To not send events to a progress set both `event_handler` and `progress_class` to `None`.

    Parameters:
    -----------
    url            (str)          : The URL to download from.
    output         (str,stream)   : The filename/filepath/stream to output to. If filename instead of path, will use currentDictory. If stream set param `stream=True`.
    stream         (bool)         : If true the output is assumed to be a stream, and `open(...)` won't be called on the output.
    event_handler  (EventHandler) : INSTANCE, The event-handler to use. (Defaulted to `EventHandler`)
    progress_class (Progress)     : NOT-INSTANCE, The progress-class to send updates to. (Defaulted to `Progress`)
    block_size     (int,"auto")   : The block-size in bytes, or "auto" to determine based on total-file-size. (Defaulted to `"auto"`)
    force_steps    (int,None)     : Calculate and send events where progress is scaled into X amount of steps.
    before_text    (str,None)     : If not `None` will print this text to stdout before the download starts. (Calls the function defined in the ´text_printer´ param with only the text param, defaulted to `None`)
    after_text     (str,None)     : If not `None` will print this text to stdout after the download completes. (Calls the function defined in the ´text_printer´ param with only the text param, defaulted to `None`)

    raise_for_status    (bool)    : If set to `True` will raise when status_code is not `200`. (Defaulted to `True`)
    on_file_exist_error (str)     : How the function should behave when the file already exists. One of "raise"/"ignore"/"ignore-with-warn"/"remove"/"remove-with-warn". (Defaulted to `"raise"`)

    progress_class_args   (list)  : `*args` to send to the progress-class when event-handler inits it. (Defaulted to `[]`)
    progress_class_kwargs (dict)  : `*kwargs` to send to the progress-class when event-handler inits it. (Defaulted to `{}`)
    requests_args         (list)  : `*args` to send to the request.get method. (Defaulted to `[]`)
    requests_kwargs       (dict)  : `*kwargs` to send to the request.get method. (Defaulted to `{}`)

    text_printer    (callable)    : The function to call when printing before and after text, will be called with only the text as a param. (Defaulted to `print`)

    handle_gdrive_vir_warn       (bool) : If the function should try to indentify GoogleDrive-Virus-Warnings and try to get the download anyway. (Only enable if you trust the URL!)
    gdrive_vir_warn_text          (str) : The text to display when a warning is identified, set to `None` to disable.
    gdrive_vir_warn_assumed_bytes (int) : The amount of bytes the warning-identifier should look at for the '<!DOCTYPE html>' prefix. Must be more then `384` bytes!
    gdrive_new_stream          (stream) : If the output is a stream and we find a stream that can't be cleared using `.seek(0)` and `.truncate(0)` (dosen't have theese properties), this will be used to init a new stream instead.

    forced_encoding (str)         : Will tell requests to use this encoding, it will otherwise make a best attempt, same for GoogleDrive-Virus-Warnings. (Should be left at None unless you know the encoding and its a non-binary file)


    Returns:
    --------
    output (str,stream) : Returns the filepath (if filepath was given it returns using the currentDirectory) or stream that was written to.
    response            : If non `200` status code.

    Raises:
    -------
    *ExcFromRequests*: If error happends during download.
    Exception:         If enabled in params, when status is not `200`.
    IsADirectoryError: If output is not a stream and is a directory.


    Info:
    -----
    For what to place in 'progress_class_args' and 'progress_class_kwargs' see the classes deffinition. `total_size`, `block_size` and `conv_bytes` is sent by the function.
    It uses `EventHandler.create_generic(...)` and `EventHandler.update_progress(...)` aswell as `EventHandler.end(..., <success>)`. (See the `EventHandler` class)
    """
    
    # Check if we should not make a event sys
    if event_handler == None or progress_class == None:
        no_events = True
    else:
        no_events = False

    # Validate output
    if stream != True:
        # Is folder?
        if os.path.dirname(output) == True:
            raise IsADirectoryError(f"Output 'output' was a directory!")

        # Check if output is filename
        if os.path.isabs(output) or os.path.dirname(output) != '':
            # Just a filename, use current directory
            output = os.path.join(os.getcwd(), output)
        
        # File already exists?
        if os.path.exists(output):
            on_file_exist_error = on_file_exist_error.lower()
            if on_file_exist_error == "raise":
                raise FileExistsError(f"Failed to download the file: '{output}'! File already exists.")
            elif on_file_exist_error == "remove" or "-with-warn" in on_file_exist_error:
                if "-with-warn" in on_file_exist_error:
                    if "remove" in on_file_exist_error:
                        print(f"File '{output}' already exists, removing.")
                    else:
                        print(f"File '{output}' already exists, ignoring.")
                if "remove" in on_file_exist_error:
                    os.remove(output)

    # Create response object
    response = requests.get(url=url, stream=True, *requests_args, **requests_kwargs)
    if forced_encoding != None: response.encoding = forced_encoding
    total_size = int(response.headers.get('content-length', 0))

    # Forced steps?
    if force_steps == None:
        total_steps = total_size
    else:
        total_steps = force_steps

    # Determine block size if necessary
    o_block_size = block_size
    if block_size == "auto":
        block_size = get_optimal_block_size(total_size)

    # Initialize the progress bar if status Is_OK
    if response.status_code == 200:
        
        # Create a progress event based on the progressClass
        if no_events == False:
            if _ovvEventId != None:
                event_id = _ovvEventId
                event_handler.update_params(event_id, total_steps=total_steps, block_size=block_size)
                event_handler.reset_progress(event_id)
            else:
                event_id = event_handler.create_generic(progress_class, total_steps=total_steps, block_size=block_size, conv_bytes=(False if force_steps != None else True), *progress_class_args,**progress_class_kwargs)
        current_size = 0
        _event_obj_cached = None

        gdrive_vir_warn_first_bytes = b''
        gdrive_vir_warn_has_checked = False

        # Iterate over stream
        try:
            if before_text not in ["",None]: text_printer(before_text)

            # Stream?
            if stream == True:
                # Use the provided stream object directly
                for data in response.iter_content(block_size):
                    # Check for early-cancelation
                    if no_events == False:
                        if _event_obj_cached == None:
                            _event_obj_cached = event_handler.get_reciever(event_id)
                        if _event_obj_cached.canceled == True:
                            raise EventCancelSenser("event.receiver.cancelled")
                    # Check for empty
                    if not data:
                        break
                    # Check for gdrive-vir-warn, google url aswell as we not having checked the start yet
                    if handle_gdrive_vir_warn == True and "drive.google" in url and gdrive_vir_warn_has_checked == False:
                        # If block_size > byteAmnt or the currentlyTraversedContent is enough
                        if block_size >= gdrive_vir_warn_assumed_bytes or current_size >= gdrive_vir_warn_assumed_bytes:
                            attempted_decoded = None
                            # Attempt conversion
                            if forced_encoding != None:
                                attempted_encoding = forced_encoding
                            else:
                                attempted_encoding = response.apparent_encoding
                            # Default if none
                            if attempted_encoding == None: attempted_encoding = "utf-8"
                            # If we entered the condition based on block_size
                            if block_size > gdrive_vir_warn_assumed_bytes:
                                attempted_decoded = data.decode(attempted_encoding, errors='ignore')
                            # Otherwise check if we have buffered bytes
                            else:
                                if len(gdrive_vir_warn_first_bytes) >= gdrive_vir_warn_assumed_bytes:
                                    attempted_decoded = gdrive_vir_warn_first_bytes.decode(attempted_encoding, errors='ignore')
                            # Check content
                            if attempted_decoded != None:
                                gdrive_vir_warn_has_checked = True
                                if attempted_decoded.startswith('<!DOCTYPE html>') and "Google Drive - Virus scan warning" in attempted_decoded:
                                    newurl = gdrive_vir_warn_url_extractor(attempted_decoded)
                                    if type(newurl) == str and newurl.strip() != "":
                                        # Before starting a new download make a new stream object
                                        if hasattr(output, 'seek') and callable(getattr(output, 'seek')) and hasattr(output, 'truncate') and callable(getattr(output, 'truncate')):
                                            output.seek(0)       # Move to the start
                                            output.truncate(0)   # Clear the content
                                            newoutput_p = output
                                        else:
                                            if gdrive_new_stream == None:
                                                raise ValueError(f"Non clearable stream-output without 'gdrive_new_stream' being set! (Use an output stream with '.seek' and '.truncate' avaliable or set 'gdrive_new_stream')")
                                            else:
                                                newoutput_p = gdrive_new_stream
                                                # Close the old one?
                                                if hasattr(output, 'close') and callable(getattr(output, 'close')):
                                                    output.close()
                                        # Reset the progressbar
                                        if no_events == False:
                                            event_handler.reset_progress(event_id)
                                        # Begin a new download
                                        newoutput = downloadFile(
                                            newurl,
                                            newoutput_p,
                                            stream,
                                            event_handler,
                                            progress_class,
                                            o_block_size,
                                            force_steps,
                                            before_text,
                                            after_text,
                                            raise_for_status,
                                            on_file_exist_error,
                                            progress_class_args,
                                            progress_class_kwargs,
                                            requests_args,
                                            requests_kwargs,
                                            text_printer,
                                            handle_gdrive_vir_warn,
                                            gdrive_vir_warn_text,
                                            gdrive_vir_warn_assumed_bytes,
                                            None,
                                            forced_encoding,
                                            event_id if no_events == False else None
                                        )
                                        if isinstance(newoutput,response.__class__):
                                            raise Exception("Attempted download of gdrive-virus-warn extracted link returned a response instead of output, most likely failed by status-code!")
                                        # After text
                                        if after_text not in ["",None]: text_printer(after_text)
                                        # Close the progress and response
                                        response.close()
                                        if no_events == False:
                                            event_handler.end(event_id,successful=True)
                                        # Return
                                        return newoutput

                        # If fails meaning our block_size is to short or we haven't traversed enough add to the shortBuffer (max at 2x of gdrive_vir_warn_assumed_bytes)
                        else:
                            gdrive_vir_warn_first_bytes += data
                    # Progress
                    output.write(data)
                    if force_steps == None:
                        current_size += len(data)
                        if no_events == False:
                            event_handler.update_progress(event_id, current_size)
                    else:
                        current_size += len(data)
                        current_steps = int(round( (current_size/total_size) *total_steps ))
                        if no_events == False:
                            event_handler.update_progress(event_id, current_steps)

            # File
            else:
                # Open a file for writing
                with open(output, "wb") as f:
                    for data in response.iter_content(block_size):
                        # Check for early-cancelation
                        if no_events == False:
                            if _event_obj_cached == None:
                                _event_obj_cached = event_handler.get_reciever(event_id)
                            if _event_obj_cached.canceled == True:
                                raise EventCancelSenser("event.receiver.cancelled")
                        # Check for empty
                        if not data:
                            break
                        # Check for gdrive-vir-warn, google url aswell as we not having checked the start yet
                        if handle_gdrive_vir_warn == True and "drive.google" in url and gdrive_vir_warn_has_checked == False:
                            # If block_size > byteAmnt or the currentlyTraversedContent is enough
                            if block_size >= gdrive_vir_warn_assumed_bytes or current_size >= gdrive_vir_warn_assumed_bytes:
                                attempted_decoded = None
                                # Attempt conversion
                                if forced_encoding != None:
                                    attempted_encoding = forced_encoding
                                else:
                                    attempted_encoding = response.apparent_encoding
                                # Default if none
                                if attempted_encoding == None: attempted_encoding = "utf-8"
                                # If we entered the condition based on block_size
                                if block_size > gdrive_vir_warn_assumed_bytes:
                                    attempted_decoded = data.decode(attempted_encoding, errors='ignore')
                                # Otherwise check if we have buffered bytes
                                else:
                                    if len(gdrive_vir_warn_first_bytes) >= gdrive_vir_warn_assumed_bytes:
                                        attempted_decoded = gdrive_vir_warn_first_bytes.decode(attempted_encoding, errors='ignore')
                                # Check content
                                if attempted_decoded != None:
                                    gdrive_vir_warn_has_checked = True
                                    if attempted_decoded.startswith('<!DOCTYPE html>') and "Google Drive - Virus scan warning" in attempted_decoded:
                                        newurl = gdrive_vir_warn_url_extractor(attempted_decoded)
                                        if type(newurl) == str and newurl.strip() != "":
                                            # Before starting a new download make sure the output dosen't exist
                                            f.close()
                                            if os.path.exists(output):
                                                os.remove(output)
                                            # Reset the progressbar
                                            if no_events == False:
                                                event_handler.reset_progress(event_id)
                                            # Begin a new download
                                            newoutput = downloadFile(
                                                newurl,
                                                output,
                                                stream,
                                                event_handler,
                                                progress_class,
                                                o_block_size,
                                                force_steps,
                                                before_text,
                                                after_text,
                                                raise_for_status,
                                                on_file_exist_error,
                                                progress_class_args,
                                                progress_class_kwargs,
                                                requests_args,
                                                requests_kwargs,
                                                text_printer,
                                                handle_gdrive_vir_warn,
                                                gdrive_vir_warn_text,
                                                gdrive_vir_warn_assumed_bytes,
                                                None,
                                                forced_encoding,
                                                event_id if no_events == False else None
                                            )
                                            if isinstance(newoutput,response.__class__):
                                                raise Exception("Attempted download of gdrive-virus-warn extracted link returned a response instead of output, most likely failed by status-code!")
                                            # After text
                                            if after_text not in ["",None]: text_printer(after_text)
                                            # Close the progress and response
                                            response.close()
                                            if no_events == False:
                                                event_handler.end(event_id,successful=True)
                                            # Return
                                            return newoutput

                            # If fails meaning our block_size is to short or we haven't traversed enough add to the shortBuffer (max at 2x of gdrive_vir_warn_assumed_bytes)
                            else:
                                gdrive_vir_warn_first_bytes += data
                        # Progress
                        f.write(data)
                        if force_steps == None:
                            current_size += len(data)
                            if no_events == False:
                                event_handler.update_progress(event_id, current_size)
                        else:
                            current_size += len(data)
                            current_steps = int(round( (current_size/total_size) *total_steps ))
                            if no_events == False:
                                event_handler.update_progress(event_id, current_steps)
            
            # After text
            if after_text not in ["",None]: text_printer(after_text)

            # Close the progress and response
            response.close()
            if no_events == False:
                event_handler.end(event_id,successful=True)

            # Return
            return output

        # Wops?
        except (KeyboardInterrupt, EventCancelSenser):
            # Close the progress and response
            response.close()
            if no_events == False:
                event_handler.end(event_id,successful=False)
            if stream == False:
                if os.path.exists(output):
                    os.remove(output)
        except Exception as e:
            # Close the progress and response
            response.close()
            if no_events == False:
                event_handler.end(event_id,successful=False)
            raise

    # Non 200 status_code
    else:
        if raise_for_status == True:
            if stream == True:
                raise Exception(f"Failed to download the file! Invalid status code ({response.status_code}).")
            else:
                raise Exception(f"Failed to download the file: '{output}'! Invalid status code ({response.status_code}).")
        else:
            return response

def fetchUrl(url, event_handler=EventHandler,progress_class=Progress, block_size="auto", force_steps=None, yield_response=False, before_text=None,after_text=None, raise_for_status=True, progress_class_args=[], progress_class_kwargs={}, requests_args=[], requests_kwargs={}, text_printer=print, handle_gdrive_vir_warn=False,gdrive_vir_warn_text="Found gdrive scan warning, attempting to extract link and download from there...",gdrive_vir_warn_assumed_bytes=384, forced_encoding=None, _ovvEventId=None):
    """
    Function over requests.get that uses an EventHandler to allow for UI/TUI visual-progress of a url-fetch.
    To just wrap requests.get and download to a file use `downloadFile`.

    To not send events to a progress set both `event_handler` and `progress_class` to `None`.

    Parameters:
    -----------
    url            (str)          : The URL to download from.
    event_handler  (EventHandler) : INSTANCE, The event-handler to use. (Defaulted to `EventHandler`)
    progress_class (Progress)     : NOT-INSTANCE, The progress-class to send updates to. (Defaulted to `Progress`)
    block_size     (int,"auto")   : The block-size in bytes, or "auto" to determine based on total-file-size. (Defaulted to `"auto"`)
    force_steps    (int,None)     : Calculate and send events where progress is scaled into X amount of steps.
    yield_response (bool)         : If `True` will return the response-object instead of `response.content`.
    before_text    (str,None)     : If not `None` will print this text to stdout before the download starts. (Calls the function defined in the ´text_printer´ param with only the text param, defaulted to `None`)
    after_text     (str,None)     : If not `None` will print this text to stdout after the download completes. (Calls the function defined in the ´text_printer´ param with only the text param, defaulted to `None`)

    raise_for_status    (bool)    : If set to `True` will raise when status_code is not `200`. (Defaulted to `True`)

    progress_class_args   (list)  : `*args` to send to the progress-class when event-handler inits it. (Defaulted to `[]`)
    progress_class_kwargs (dict)  : `*kwargs` to send to the progress-class when event-handler inits it. (Defaulted to `{}`)
    requests_args         (list)  : `*args` to send to the request.get method. (Defaulted to `[]`)
    requests_kwargs       (dict)  : `*kwargs` to send to the request.get method. (Defaulted to `{}`)

    text_printer    (callable)    : The function to call when printing before and after text, will be called with only the text as a param. (Defaulted to `print`)

    handle_gdrive_vir_warn       (bool) : If the function should try to indentify GoogleDrive-Virus-Warnings and try to get the download anyway. (Only enable if you trust the URL!)
    gdrive_vir_warn_text          (str) : The text to display when a warning is identified, set to `None` to disable.
    gdrive_vir_warn_assumed_bytes (int) : The amount of bytes the warning-identifier should look at for the '<!DOCTYPE html>' prefix. Must be more then `384` bytes!

    forced_encoding (str)         : Will tell requests to use this encoding, it will otherwise make a best attempt, same for GoogleDrive-Virus-Warnings. (Should be left at None unless you know the encoding and its a non-binary file)


    Returns:
    --------
    content  : If `yield_response` is `False`.
    response : If non `200` status code or `yield_response` is `True`.

    Raises:
    -------
    *ExcFromRequests*: If error happends during fetching.
    Exception:         If enabled in params, when status is not `200`.

    Info:
    -----
    For what to place in 'progress_class_args' and 'progress_class_kwargs' see the classes deffinition. `total_size`, `block_size` and `conv_bytes` is sent by the function.
    It uses `EventHandler.create_generic(...)` and `EventHandler.update_progress(...)` aswell as `EventHandler.end(..., <success>)`. (See the `EventHandler` class)
    """
    
    # Check if we should not make a event sys
    if event_handler == None or progress_class == None:
        no_events = True
    else:
        no_events = False

    # Create response object
    response = requests.get(url=url, stream=True, *requests_args, **requests_kwargs)
    if forced_encoding != None: response.encoding = forced_encoding
    total_size = int(response.headers.get('content-length', 0))

    # Forced steps?
    if force_steps == None:
        total_steps = total_size
    else:
        total_steps = force_steps

    # Determine block size if necessary
    o_block_size = block_size
    if block_size == "auto":
        block_size = get_optimal_block_size(total_size)

    # Initialize the progress bar if status Is_OK
    if response.status_code == 200:
        
        # Create a progress event based on the progressClass
        if no_events == False:
            if _ovvEventId != None:
                event_id = _ovvEventId
                event_handler.update_params(event_id, total_steps=total_steps, block_size=block_size)
                event_handler.reset_progress(event_id)
            else:
                event_id = event_handler.create_generic(progress_class, total_steps=total_steps, block_size=block_size, conv_bytes=(False if force_steps != None else True), *progress_class_args,**progress_class_kwargs)

        _event_obj_cached = None

        content_buffer = b''

        gdrive_vir_warn_has_checked = False

        # Iterate over stream
        try:
            if before_text not in ["",None]: text_printer(before_text)

            # Work
            for data in response.iter_content(block_size):
                # Check for early-cancelation
                if no_events == False:
                    if _event_obj_cached == None:
                        _event_obj_cached = event_handler.get_reciever(event_id)
                    if _event_obj_cached.canceled == True:
                        raise EventCancelSenser("event.receiver.cancelled")
                # Check for empty
                if not data:
                    break
                # Check for gdrive-vir-warn, google url aswell as we not having checked the start yet
                if handle_gdrive_vir_warn == True and "drive.google" in url and gdrive_vir_warn_has_checked == False:
                    # If block_size > byteAmnt or the currentlyTraversedContent is enough
                    if block_size >= gdrive_vir_warn_assumed_bytes or len(content_buffer) >= gdrive_vir_warn_assumed_bytes:
                        attempted_decoded = None
                        # Attempt conversion
                        if forced_encoding != None:
                            attempted_encoding = forced_encoding
                        else:
                            attempted_encoding = response.apparent_encoding
                        # Default if none
                        if attempted_encoding == None: attempted_encoding = "utf-8"
                        # If we entered the condition based on block_size
                        if block_size > gdrive_vir_warn_assumed_bytes:
                            attempted_decoded = data.decode(attempted_encoding, errors='ignore')
                        # Otherwise check if we have buffered bytes
                        else:
                            attempted_decoded = content_buffer.decode(attempted_encoding, errors='ignore')
                        # Check content
                        if attempted_decoded != None:
                            gdrive_vir_warn_has_checked = True
                            if attempted_decoded.startswith('<!DOCTYPE html>') and "Google Drive - Virus scan warning" in attempted_decoded:
                                newurl = gdrive_vir_warn_url_extractor(attempted_decoded)
                                if type(newurl) == str and newurl.strip() != "":
                                    # Before starting a new download empty the buffer
                                    #del content_buffer
                                    #content_buffer = b''
                                    # Reset the progressbar
                                    if no_events == False:
                                        event_handler.reset_progress(event_id)
                                    # Begin a new download
                                    newcontent = fetchUrl(
                                        newurl,
                                        event_handler,
                                        progress_class,
                                        o_block_size,
                                        force_steps,
                                        yield_response,
                                        before_text,
                                        after_text,
                                        raise_for_status,
                                        progress_class_args,
                                        progress_class_kwargs,
                                        requests_args,
                                        requests_kwargs,
                                        text_printer,
                                        handle_gdrive_vir_warn,
                                        gdrive_vir_warn_text,
                                        gdrive_vir_warn_assumed_bytes,
                                        forced_encoding,
                                        event_id if no_events == False else None
                                    )
                                    if isinstance(newcontent,response.__class__):
                                        raise Exception("Attempted download of gdrive-virus-warn extracted link returned a response instead of output, most likely failed by status-code!")
                                    # After text
                                    if after_text not in ["",None]: text_printer(after_text)
                                    # Close the progress and response
                                    response.close()
                                    if no_events == False:
                                        event_handler.end(event_id,successful=True)
                                    # Return
                                    return newcontent
                # Progress
                content_buffer += data
                if force_steps == None:
                    current_steps = int(round( (len(content_buffer)/total_size) *total_steps ))
                    if no_events == False:
                        handler.update_progress(event_id, current_steps)
                else:
                    if no_events == False:
                        handler.update_progress(event_id, len(content_buffer))
            
            # After Text
            if after_text not in ["",None]: text_printer(after_text)

            # Close the progress and response
            response.close()
            if no_events == False:
                event_handler.end(event_id,successful=True)

            # Return
            if yield_response == True:
                # Return the response object with downloaded content
                response._content = content_buffer
                return response
            else:
                return content_buffer

        # Wops?
        except (KeyboardInterrupt, EventCancelSenser):
            # Close the progress and response
            response.close()
            if no_events == False:
                event_handler.end(event_id,successful=False)
        except Exception as e:
            # Close the progress and response
            response.close()
            if no_events == False:
                event_handler.end(event_id,successful=False)
            raise

    # Non 200 status_code
    else:
        if raise_for_status == True:
            raise Exception(f"Failed to fetch url, invalid status code ({response.status_code})!")
        else:
            return response