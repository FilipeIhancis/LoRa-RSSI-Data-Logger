# ----------------------------------------------------------------------------------------------------------------
#   LoRa RSSI Data Logger / LoRa Range Measurement Tool with Statistics and Data Logging
#   Simple LoRa RSSI Data Logger for technical visits
#   Filipe Ihancis Teixeira (filipeihancist@gmail.com)
# ----------------------------------------------------------------------------------------------------------------


import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from serial import Serial
import serial.tools.list_ports
import statistics
import csv
import os
import time


# Generate log file ----------------------------------------------------------------------------------------------

def gen_log_file():

    # confirms whether the user really wants to generate a log file
    choice = messagebox.askyesno("Gen. log file", "Do you want to continue and gen the log?")
    if not choice:
        return

    # Gets arq name and COM
    FILE_NAME = str(entry_file_name.get())
    PORT = str(box_select_COM.get())
    
    # Does not proceed if the user has not entered the file name and set the COM port
    if(FILE_NAME == "" or PORT == ""):
       print("Error: File names not filled in")
       messagebox.showerror("Error!", "File names not filled in")
       window.update_idletasks()
       return
    
    # Formats the names of the port and destination file
    PORT = PORT.split(" ")[0]
    FILE_NAME += ".txt"
    LOG_SAMPLING_TIME = int(box_sampling_time.get())
    
    try:
        # Create Serial object:
        # OBS: default setting for Arduino IDE
        ser = Serial(PORT)
        ser.close()
        ser.baudrate = 9600
        ser.port = PORT
        ser.bytesize = 8
        ser.parity = 'N'
        ser.stopbits = 1
        ser.timeout = 0.1
        ser.open()
        ser.reset_input_buffer()
    except:
        print("Error: COM port not accessed")
        messagebox.showerror("Error!", "COM port not accessed")
        window.update_idletasks()
        return
    
    # Generates header in log:
    gen_header_log(FILE_NAME, LOG_SAMPLING_TIME)
        
    # Configure progress bar
    progress['value'] = 0
    progress['maximum'] = 100

    # Starts the timer
    startTime = time.time()
    elapsedTime = 0
    window.update_idletasks()

    while True:
        try:
            # Reads a complete line from the COM (serial) port
            N = ser.in_waiting        
            data = ser.readline(-1) 
            data = data.decode('utf-8')
        except KeyboardInterrupt:
            # If you are in the terminal, you can stop the loop by force
            break
        except Exception as e:
            pass
        else:
            # Updates timer and progress bar
            elapsedTime = time.time() - startTime
            progress_value = (elapsedTime / LOG_SAMPLING_TIME) * 100
            progress['value'] = min(progress_value, 100)
            window.update_idletasks()

            # Stores data in the file
            if(data != ""):
                print(data)
                file = open(FILE_NAME, "a")
                file.write(data + "\n")
        finally:
            # Ends RSSI collection after specified time
            if elapsedTime >= LOG_SAMPLING_TIME:
                window.update_idletasks()
                messagebox.showinfo("Info", "Log completed.")
                print("Log completed.\Elapsed time: ", elapsedTime, sep = "")
                break

    # ends serial monitoring and progress bar
    file.close()
    ser.close()
    progress['value'] = 0
    return


# Write header ---------------------------------------------------------------------------------------------------------

def gen_header_log(file_name, log_time):

    # formats timestamp and location (point coordinates)
    timestamp_init = time.strftime("%Y-%m-%d %H:%M:%S")
    lat_l1 = entry_lat_lora1.get() if entry_lat_lora1.get() != "" else set_coordinates_zero()
    long_l1 = entry_long_lora1.get() if entry_long_lora1.get() != "" else set_coordinates_zero()
    lat_l2 = entry_lat_lora2.get() if entry_lat_lora2.get() != "" else set_coordinates_zero()
    long_l2 = entry_long_lora2.get() if entry_long_lora2.get() != "" else set_coordinates_zero()

    # Write the header in log file
    with open(file_name, "a") as file:
        file.write(f"LOG_INFO\n")
        file.write(f"LAT_LORA1: {lat_l1}\nLONG_LORA1: {long_l1}\nLAT_LORA2: {lat_l2}\nLONG_LORA2: {long_l2}\n")
        file.write(f"START_OF_LOG: {timestamp_init}\nLOG_SAMPLING_TIME: {log_time}\n\n")
    file.close()
    return


# Updates serial ports --------------------------------------------------------------------------------------------------

def update_COM_ports():
    
    # List of available ports
    ports = serial.tools.list_ports.comports()
    box_select_COM['values'] = ports

    # If there are no ports available, it displays “none”
    if(ports):
        box_select_COM.set(ports[0])
    else:
        box_select_COM.set('None')
    window.update_idletasks()
    return


# Sets coordinates to zero ---------------------------------------------------------------------------------------------------

def set_coordinates_zero():
    entry_lat_lora1.delete(0,tk.END)
    entry_lat_lora1.insert(0, "-00.000000")
    entry_long_lora1.delete(0,tk.END)
    entry_long_lora1.insert(0, "-00.000000")
    entry_lat_lora2.delete(0,tk.END)
    entry_lat_lora2.insert(0, "-00.000000")
    entry_long_lora2.delete(0,tk.END)
    entry_long_lora2.insert(0, "-00.000000")
    return "-00.000000"


# Save statistics -------------------------------------------------------------------------------------------------------------

def save_stats(id, mean, std):

    # Table header names
    header = ['ID', 'AVG', 'STD', 'LAT_L1', 'LONG_L1', 'LAT_L2', 'LONG_L2', 'START', 'LOG_SAMPLING_TIME']
    info = {}

    # Reading data stored in the log file
    with open(id+".txt", 'r') as file:
        for line in file:
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()

    # Extracting values ​​for specific variables
    lat_lora1 = info.get("LAT_LORA1")
    long_lora1 = info.get("LONG_LORA1")
    lat_lora2 = info.get("LAT_LORA2")
    long_lora2 = info.get("LONG_LORA2")
    start_of_log = info.get("START_OF_LOG")
    log_sampling_time = info.get("LOG_SAMPLING_TIME")

    # Format log in tabular text format
    line_stats = f"{id},{mean},{std},{lat_lora1},{long_lora1},{lat_lora2},{long_lora2},{start_of_log},{log_sampling_time}\n"

    # Saves to a .csv file
    stats_file = "stats.csv"
    stats_file_exists = os.path.exists(stats_file)

    with open(stats_file, "a", newline='') as file:
        writer = csv.writer(file)
        # Creates the header if the file does not exist in the directory
        if not stats_file_exists:
            writer.writerow(header)
            file.write(line_stats)
        else:
            file.write(line_stats)

    return


# Generates statistics ----------------------------------------------------------------------------------------------------------

def get_stats_rssi():

    # Checks if the file exists or is valid
    FILE_NAME = str(entry_file_name.get())
    if(FILE_NAME == ""):
        messagebox.showerror("Error!", "Please enter a valid file name")
        window.update_idletasks()
        print("Error: Enter file name")
        return
    FILE_NAME += ".txt"

    try:
        # Open the file and read the lines
        with open(FILE_NAME, "r") as file:
            lines = file.readlines()

        # LoRa messages to detect
        rssiValues = []
        wantedMessages = [
            "Mensagem recebida: Hello im random sender. RSSI: ",
            "Mensagem enviada: Hello im random sender. RSSI: "
        ]

        # Searches for the desired LoRa messages in each line of the file
        for line in lines:
            for msg in wantedMessages:
                if msg in line:
                    try:
                        # Collect the rssi value
                        rssi = int(line.split(msg)[1].strip())
                        rssiValues.append(rssi)
                    except ValueError:
                        print(f"Invalid value found in line {line}")

        # Statistical calculation
        RssiMean = statistics.mean(rssiValues) if rssiValues else 0
        RssiStd = statistics.stdev(rssiValues) if len(rssiValues) > 1 else 0

        # Formats data to string
        RssiMean_str = "Mean: " + str(round(RssiMean,4))
        RssiStd_str = "Std: " + str(round(RssiStd,4))

        # Update labels
        lbl_avg_rssi.config(text = RssiMean_str)
        lbl_std_rssi.config(text = RssiStd_str)

        # saves statistics in a csv file
        file.close()
        save_stats(entry_file_name.get(), RssiMean, RssiStd)
        window.update_idletasks()
        messagebox.showinfo("Info", "Statistics saved successfully")
        
    except FileNotFoundError:
        print("Error: file does not exist")
        messagebox.showerror("Error!", "File does not exist")
        window.update_idletasks()
        return
    return


# SETUP WINDOW -----------------------------------------------------------------------------------------------------------

window = tk.Tk()
window.title("Coleta RSSI LoRa")
window.resizable(width = False, height = False)
main_frm = tk.Frame(master = window)
main_frm.grid(row = 0, column = 0, padx = 10, pady = 10)
style = ttk.Style(window)
style.theme_use("clam")

# Defines a title
lbl_title = tk.Label(master = main_frm, font=["Arial", "11", "bold"], text = "LoRa RSSI Data Logger")
lbl_title.grid(row = 0, column = 0, columnspan = 7, pady = 1)


# LOG CONFIG SECTION --------------------------------------------------------------------------------------------------------------

# Creates a frame for the section
log_config = tk.LabelFrame(main_frm, text = "Log config", relief = "groove", font=("Arial", 9, "bold"))
log_config.grid(row = 1, rowspan = 5, column = 0, columnspan = 2, pady = 5)

# Choose a log file name
lbl_file_name = tk.Label(master = log_config, text = "Log/File name", pady = 3)
lbl_file_name.grid(row = 1, column = 0, sticky = "w")
entry_file_name = tk.Entry(master = log_config, width = 15)
entry_file_name.grid(row = 1, column = 1, sticky = "e", padx = 5)

# Select COM port
lbl_port_COM = tk.Label(master = log_config, text = "Select COM")
box_select_COM = ttk.Combobox(master = log_config, width= 10)
lbl_port_COM.grid(row = 2, column = 0, sticky = "w", pady = 1)
box_select_COM.grid(row = 2, column = 1, sticky = "e", padx = 5)
box_select_COM.bind("<<ComboboxSelected>>")

# Sampling time in seconds
lbl_rssi_samp_time = tk.Label(master = log_config, text = "Sampling time (s)")
lbl_rssi_samp_time.grid(row = 3, column = 0, sticky = "w", pady = 1)
box_sampling_time = ttk.Combobox(master = log_config, width= 5, values = [10,15,20,25,30,35,40,45])
box_sampling_time.grid(row = 3, column= 1, sticky = "e", padx = 5)
box_sampling_time.set(20)

# Update COM button
btn_updt_COM = tk.Button(master = log_config, text = "Update COMs", command = update_COM_ports, relief = "groove")
btn_updt_COM.config(bg = "lightblue")
btn_updt_COM.grid(row = 4, column=0, sticky = "w", pady = 5, padx = 5)

# Generates log file button
btn_log = tk.Button(master = log_config, text = "Get log", command = gen_log_file, relief = "groove")
btn_log.config(width = 10, bg= "lightblue")
btn_log.grid(row = 4, column = 1, sticky = "e", pady = 5, padx = 5)

# Progress bar
progress = ttk.Progressbar(master = log_config, orient = "horizontal", length = 150, mode = "determinate")
progress.grid(row = 5, column = 0, columnspan = 2, pady = 5)


# TRANSCEIVER COORDINATES INFO SECTION -----------------------------------------------------------------------------------------------

# Creates the frames for the section
lora1_frm = tk.LabelFrame(main_frm, text = "LoRa 1 transceiver coordinates", relief = "groove", font=("Arial", 8, "bold"))
lora1_frm.grid(row = 1, rowspan = 2, column = 3, padx = 20)
lora2_frm = tk.LabelFrame(main_frm, text = "LoRa 2 transceiver coordinates", relief = "groove", font=("Arial", 8, "bold"))
lora2_frm.grid(row = 3, rowspan = 2, column = 3, padx = 20)

# Creates coordinates labels
lbl_lat = tk.Label(master = lora1_frm, text = "Latitude").grid(row = 1, column = 3, sticky = "w")
lbl_long = tk.Label(master = lora1_frm, text = "Longitude").grid(row = 2, column = 3, sticky = "e")
lbl_lat = tk.Label(master = lora2_frm, text = "Latitude").grid(row = 3, column = 3, sticky = "w")
lbl_long = tk.Label(master = lora2_frm, text = "Longitude").grid(row = 4, column = 3, sticky = "e")

# Choose the coordinates
entry_lat_lora1 = tk.Entry(master = lora1_frm, width = 20)
entry_lat_lora1.grid(row = 1, column = 4, padx = 5)
entry_long_lora1 = tk.Entry(master = lora1_frm, width = 20)
entry_long_lora1.grid(row = 2, column = 4, padx = 5)
entry_lat_lora2 = tk.Entry(master = lora2_frm, width = 20)
entry_lat_lora2.grid(row = 3, column = 4, padx = 5)
entry_long_lora2 = tk.Entry(master = lora2_frm, width = 20)
entry_long_lora2.grid(row = 4, column = 4, padx = 5)


# GENERATES LOG STATISTICS SECTION ----------------------------------------------------------------------------------------------------

# Creates the frame for the section
stats_frm = tk.LabelFrame(main_frm, text = "Log statistics (.csv)", relief = "groove", font=("Arial", 9, "bold"))
stats_frm.grid(row = 1, rowspan = 2, column = 5, columnspan = 2)

# Gen Statistics button
btn_get_stats = tk.Button(master = stats_frm, text = "Gen Statistics", command = get_stats_rssi)
btn_get_stats.config(relief = "groove", width = 13, bg = "lightblue")
btn_get_stats.grid(row = 1, column = 5, sticky = "s", pady = 3, columnspan = 2)

# Creates statistics labels
avg_rssi_frame = tk.LabelFrame(master = stats_frm, text = "Mean", relief = "groove", font=("Arial", 8))
avg_rssi_frame.grid(row = 2, column = 5)
std_rssi_frame = tk.LabelFrame(master = stats_frm, text = "Std", relief = "groove", font=("Arial", 8))
std_rssi_frame.grid(row = 2, column = 6)
lbl_avg_rssi = tk.Label(master = avg_rssi_frame, text = "----")
lbl_avg_rssi.grid(row = 2, column = 5, sticky = "w", padx = 30)
lbl_std_rssi = tk.Label(master = std_rssi_frame, text = "----")
lbl_std_rssi.grid(row = 2, column = 6, sticky = "e", padx = 30)


# END OF STYLING AND SETUP -------------------------------------------------------------------------------------------------------------

update_COM_ports()
set_coordinates_zero()
window.mainloop()