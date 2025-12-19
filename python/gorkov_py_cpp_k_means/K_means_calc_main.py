# imports
import flet
from flet import (
    Page, AppBar, BottomSheet,
    Column, Row, Stack,
    Container, Image,
    Text, TextField, Icon,
    ElevatedButton, OutlinedButton,
    Dropdown, Switch,
    PopupMenuButton, PopupMenuItem,
    icons, Radio, RadioGroup, FilePicker, Checkbox, WebView
)
import threading
import subprocess
import json
import csv
import ast
import os
import sys
#import tempfile
#import asyncio # for flet async

# for new graphing fn
import plotly.graph_objects as go


# for the graph for old graphing fn
import matplotlib
#matplotlib.use("Agg") # if active is stops the interactive graph from showing but fixes the tkinter problems
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D

# TODO : fix the 3d visualisation


# global vars
global_calc_out = None # the result of the calculation for k-maens
global_calculation_complete = False
global_plt_obj = None
global_fig_obj = None

# global calc vars
global_ch_index_res = ""
global_centers_res = ""
global_cluster_list_res = []

# path vars
global_k_means_exe_path = "release_build_v1.0.exe"

# functions outside the ui


def main(page: Page):
    
    # page setup
    page.title = "K-means"
    page.theme_mode = "light"
    page.padding = 15
    page.window_resizable = True
    page.vertical_alignment = flet.alignment.center
    page.horizontal_alignment = flet.alignment.center
    page.scroll = True

    # vars

    # functions in app

    # fn to convert data for graph
    def convert_data_for_graph():
        print("Called fn to convert data for graph and call the graph")

        # cluster
        clusters = {
            f"C{i}": cluster
            for i, cluster in enumerate(global_cluster_list_res)
        }

        # centers
        centroids = global_centers_res

        #show_3d_graph_of_calculation_old(clusters,centroids,"X","Y","Z","Placeholder")
        show_3d_graph_plotly_browser(clusters,centroids,"K-means graph 3D")

    # new fn to put the graph in webvier(notusable)
    """def show_3d_graph_plotly_webview(cluster_results, centers=None, x_lable="x", y_label="y", z_label="z", title="graph title"):
        
        print("Running new graphing fn... in webview")
        
        fields = [x_lable, y_label, z_label]
        
        fig = go.Figure()
        
        cluster_names = list(cluster_results.keys())
        
        for i, cluster_name in enumerate(cluster_names):
            
            points = cluster_results[cluster_name]
            
            if not points:
                continue
            
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            zs = [p[2] for p in points]
            
            # cluster points
            fig.add_trace(
                go.Scatter3d(
                    x=xs,
                    y=ys,
                    z=zs,
                    mode="markers",
                    name=cluster_name,
                    marker=dict(size=4, opacity=0.6),
                )
            )
            
            # centroid (if provided)
            if centers and i < len(centers):
                cx, cy, cz = centers[i]
                fig.add_trace(
                    go.Scatter3d(
                        x=[cx],
                        y=[cy],
                        z=[cz],
                        mode="markers",
                        name=f"{cluster_name} center",
                        marker=dict(
                            size=2,
                            symbol="x",
                            color="black"
                        ),
                    )
                )
        
        fig.update_layout(
            title=title,
            scene=dict(
                xaxis_title=fields[0] if fields else "X",
                yaxis_title=fields[1] if fields else "Y",
                zaxis_title=fields[2] if fields else "Z",
                ),
                margin=dict(l=0, r=0, b=0, t=40),
                legend_title="Clusters",
            )
        
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        fig.write_html(tmp.name)

        graph_webview.url = f"file:///{tmp.name.replace(os.sep, '/')}"
        page.update()
    """
    
    # new fn to draw the graph using plotly (webbrowser)
    def show_3d_graph_plotly_browser(cluster_results, centers=None, title="graph title"):
        
        # global var
        global global_fig_obj
        
        print("Running new graphing fn...")
        
        fields_fn_res = get_selected_fields()
        print("Selected fields :")
        print(fields_fn_res)
        
        fields = fields_fn_res
        
        fig = go.Figure()

        #global_fig_obj = fig
        
        cluster_names = list(cluster_results.keys())
        
        for i, cluster_name in enumerate(cluster_names):
            
            points = cluster_results[cluster_name]
            
            if not points:
                continue
            
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            zs = [p[2] for p in points]
            
            # cluster points
            fig.add_trace(
                go.Scatter3d(
                    x=xs,
                    y=ys,
                    z=zs,
                    mode="markers",
                    name=cluster_name,
                    marker=dict(size=4, opacity=0.6),
                )
            )
            
            # centroid (if provided)
            if centers and i < len(centers):
                cx, cy, cz = centers[i]
                fig.add_trace(
                    go.Scatter3d(
                        x=[cx],
                        y=[cy],
                        z=[cz],
                        mode="markers",
                        name=f"{cluster_name} center",
                        marker=dict(
                            size=2,
                            symbol="x",
                            color="black"
                        ),
                    )
                )
        
        fig.update_layout(
            title=title,
            scene=dict(
                xaxis_title=fields[0] if fields else "X",
                yaxis_title=fields[1] if fields else "Y",
                zaxis_title=fields[2] if fields else "Z",
                ),
                margin=dict(l=0, r=0, b=0, t=40),
                legend_title="Clusters",
            )
        
        fig.show()
        del fig
        #global_fig_obj.show()
    
    # fn to draw the graph
    def show_3d_graph_of_calculation_old(clusters, centroids, X_lable, Y_label, Z_label, graph_title):
        print("Running graphing fn....")

        # global vars
        global global_plt_obj

        global_plt_obj = plt
        
        # plotting
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection="3d")
        
        # color definitions
        colors = matplotlib.colormaps.get_cmap("tab10").resampled(len(clusters))
        
        # enum clusters and assing label
        for i, (cluster_name, points) in enumerate(clusters.items()):
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            zs = [p[2] for p in points]
            
            ax.scatter(xs, ys, zs, color=colors(i), label=cluster_name, alpha=0.6)
        
        # Plot centroids
        for c in centroids:
            ax.scatter(c[0], c[1], c[2], color="black", s=150, marker="x")
        
        
        # set the labels for the axis x,y,z
        
        # x
        ax.set_xlabel(X_lable)
        
        # y
        ax.set_ylabel(Y_label)
        
        # z
        ax.set_zlabel(Z_label)
        
        ax.set_title(graph_title)
        ax.legend()
        
        # finally show the graph
        global_plt_obj.show()

    # parse the result from run_kmeans_exe and seperate it into variables
    def split_ch_and_centers(raw: str):
        
        # global vars
        global global_ch_index_res
        global global_centers_res
        global global_cluster_list_res
        
        print("Running fn to split the result into 2 vars...")
        
        if isinstance(raw, dict):
            data = raw
        else:
            data = ast.literal_eval(raw)
        
        global_ch_index_res = data["CH_index"]
        global_centers_res = data["centers"]
        
        # Collect C0, C1, C2, ...
        i = 0
        while True:
            key = f"C{i}"
            if key not in data:
                break
            global_cluster_list_res.append(data[key])
            i += 1
        
        print("Values assigned printing...")
        print(global_ch_index_res)
        print(global_centers_res)
        print(global_cluster_list_res)
        set_results_values()
        hide_input_layout_show_result()
        if (auto_open_graph.value):
            convert_data_for_graph()
    
    
    # full exe function to call the alogrithm
    def run_kmeans_exe(exe_path: str, dataset_path: str, num_clusters: int, fields: list[str] | None = None, centers: list[dict] | None = None,) -> dict:
        print("Running k-means exe fn with parametars...")
        print(dataset_path)
        print(num_clusters)
        print(fields)
        print("Centers for exe are :")
        print(centers)
        
        # global var
        global global_calc_out
        global global_calculation_complete
        
        # validation
        if not dataset_path:
            raise ValueError("dataset_path is required")
        
        if not isinstance(num_clusters, int) or num_clusters <= 0:
            raise ValueError("numClusters must be a positive integer")
        
        
        if fields:
            if not isinstance(fields, list):
                raise ValueError("fields must be a list")
            if len(fields) > 3:
                raise ValueError("Maximum of 3 fields allowed")
        
        if centers:
            if not isinstance(centers, list):
                raise ValueError("centers must be a list")
            for c in centers:
                if not isinstance(c, dict):
                    raise ValueError("Each center must be a dict")
        
        # build JSON for gorkov c++ algo
        payload = {
            "dataset": dataset_path,
            "numClusters": num_clusters,
        }
        
        if fields:
            payload["fields"] = fields
        
        # if centers is None or empty auto-select in C++
        if centers:
            payload["centers"] = centers
        
        input_json = json.dumps(payload)
        
        # run exe
        process = subprocess.Popen(
            exe_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        
        stdout, stderr = process.communicate(input_json)
        
        if process.returncode != 0:
            raise RuntimeError(f"K-means executable failed (code {process.returncode}):\n{stderr}")
        
        # handle UTF-8 BOM
        stdout = stdout.lstrip("\ufeff")
        
        # parse output JSON
        try:
            #return json.loads(stdout)
            result = json.loads(stdout)
            global_calc_out = result
            print("From k-means exe fn > result calculated")
            global_calculation_complete = True
            print(global_calc_out)
            split_ch_and_centers(global_calc_out)
        except json.JSONDecodeError as e:
            print("From k-means exe fn > error")
            raise RuntimeError(f"Failed to parse EXE output as JSON:\n{stdout}") from e
    
    # fn to set the result values
    def set_results_values():
        print("Fn called to set the result values!!")
        ch_index_label.value = "Index : " + reduce_string(str(global_ch_index_res),150)
        centers_label.value = "Centers positions : " + reduce_string(str(global_centers_res),150)
        clusters_label.value = "Clusters values : " + reduce_string(str(global_cluster_list_res),150)
        page.update()
    
    # fn to recuce the text
    def reduce_string(text: str, keep: int) -> str:
        if not text or keep <= 0:
            return "..."
        
        if len(text) <= keep:
            return text
        
        return text[:keep + 1] + "..."
    
    # get current selected fields
    def get_selected_fields() -> list[str]:
        return [
            cb.label
            for cb in fields_column.controls
            if cb.value
        ]
    
    # fn for running the kmeans
    
    def run_k_means_start_thread():
        print("Called function to run k-means algorithm...")
        if (dataset_tb.value != "" and int(number_of_clusters_txtb.value) > 0 and get_selected_fields() != None):
            k_means_thread = threading.Thread(target=run_kmeans_exe, args=(global_k_means_exe_path, dataset_tb.value, int(number_of_clusters_txtb.value), get_selected_fields(), get_centers_or_none()))
            k_means_thread.start()
            print("Started k-means thread")
        else:
            print("Insufficient data!!!")

    # get centers fn
    def get_centers_or_none():
        
        centers = []
        
        # Skip title + spacer (first 2 controls)
        for tf in coordinates_column.controls[2:]:
            
            value = (tf.value or "").strip()
            
            # Empty field → auto-select
            if not value:
                return None
            
            # Expect format: x,y or x,y,z
            parts = [p.strip() for p in value.split(",")]
            
            if len(parts) > 3 or len(parts) < 1:
                return None
            
            try:
                nums = [float(p) for p in parts]
            except ValueError:
                return None
            
            center = {}
            
            if len(nums) >= 1:
                center["x"] = nums[0]
            if len(nums) >= 2:
                center["y"] = nums[1]
            if len(nums) == 3:
                center["z"] = nums[2]
            
            centers.append(center)
        
        return centers if centers else None

    # csv file fn

    def get_csv_fields(csv_path: str) -> list[str]:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
        return headers
    
    def build_fields_selector(headers: list[str]):
        fields_column.controls.clear()
        
        for h in headers:
            fields_column.controls.append(
                flet.Checkbox(label=h, value=False, on_change=fields_changed)
            )
        page.update()
    
    def fields_changed(e):
        selected = [
            cb.label
            for cb in fields_column.controls
            if cb.value
        ]
        
        if len(selected) > 3:
            e.control.value = False
            page.update()
            return
    
    # file picker functions

    # fn to call when the dataset has been picked
    def dataset_picked(e: flet.FilePickerResultEvent):
        if not e.files:
            return
        
        path = e.files[0].path
        dataset_tb.value = path
        
        headers = get_csv_fields(path)
        build_fields_selector(headers)
        
        page.update()

    # open the file picker
    def open_dataset_picker():
        print("Called file picker fn")
        file_picker.pick_files(
            allow_multiple=False,
            file_type=flet.FilePickerFileType.CUSTOM,
            allowed_extensions=["csv"],
        )
    
    # fn for radio group
    def radio_group_change(e):
        print("Radio group change triggered !!!")
        print("Currently selected group value : " + radio_group.value)
        
        if (int(radio_group.value) == 1):
            print("Selected : Self-select")
            coordinates_layout.visible = True
        if (int(radio_group.value) == 2):
            print("Selected : Auto-select")
            coordinates_layout.visible = False
        
        page.update()
    
    # fn to dynamicly generate the N number of textFields
    def generate_coordinate_fields(n: int):
        print("Running textfiled generate function for " + str(n) + " number of textfields")

        # keep title + spacer
        coordinates_column.controls = coordinates_column.controls[:2]
        
        for i in range(n):
            coordinates_column.controls.append(
                TextField(
                    hint_text=f"Cluster {i + 1} coordinates",
                    width=600,
                    border_radius=15,
                )
            )
        
        page.update()
        print("ran the fn. Page update called !!")

    # fn to run when number of clusters changes
    def on_num_clusters_change(e):
        print("Running fn for when number of clusters changes...")
        tb_value = e.control.value

        if not tb_value.isdigit():
            return
        
        n = int(tb_value)

        generate_coordinate_fields(n)

    # open dataset button
    def open_button_fn(e):
        print("Open button pressed !!!")
        open_dataset_picker()

    # start button function
    def start_btn_fn(e):
        print("Start button pressed !!!")
        run_k_means_start_thread()
        #page.run_task(set_results_async)
        #hide_input_layout_show_result()

    def return_btn_fn(e):
        print("Return btn fn called !!!")

        # global var
        global global_calculation_complete
        global global_ch_index_res
        global global_centers_res
        global global_cluster_list_res

        global_calculation_complete = False
        global_ch_index_res = ""
        global_centers_res = ""
        global_cluster_list_res = []
        #global_plt_obj.close("all") # old close graph call from mathplotlib (hanging thread issue)
        
        hide_result_layout_show_input_section()

    # show result layout fn
    def hide_input_layout_show_result():
        print("Called fn to hide input layout and show result")
        input_section_layout.visible = False
        result_layout.visible = True
        page.update()
    
    # hide result layout fn
    def hide_result_layout_show_input_section():
        print("Called fn to hide result layout and show input section")
        input_section_layout.visible = True
        result_layout.visible = False
        page.update()
    
    # change theme btn
    def change_theme_fn():
        print("Change theme fn called !!")
        if (page.theme_mode == "light"):
            page.theme_mode = "dark"
        else:
            page.theme_mode = "light"
        page.update()
    
    def fn_for_change_theme_menu_btn(e):
        print("Menu button pressed fn called !!!")
        change_theme_fn()
    
    # fn for showing graph btn
    def show_graph_btn_fn(e):
        print("Pressed show graph button!!!")
        convert_data_for_graph()
    
    # fn to restart the app
    def restart_app():
        print("Restart fn app called !!!")
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    
    # switch for menu
    auto_open_graph = Switch()
    auto_open_graph.value = True

    # app bar
    page.appbar = AppBar(
        #bgcolor="#1A1C1E",
        title=Text("K-means calculator", size=22,font_family="Roboto",weight=flet.FontWeight.BOLD),
        actions=[
            PopupMenuButton(
                items=[
                    PopupMenuItem(icon=flet.icons.DARK_MODE,text="Change theme",on_click=fn_for_change_theme_menu_btn),
                    # switch menu btn
                    PopupMenuItem(
                        #on_click=popup_menu_action_cover_art_switch_change,
                        content= Row(
                            [
                                Text("Auto open graph"),
                                auto_open_graph,
                            ]
                        ),
                    ),
                    PopupMenuItem(text="Version : 1.0v"),
                ]
            )
        ],
    )

    # core widgets
    
    # dataset layout
    open_dataset_btn = ElevatedButton(
        text="Open",
        bgcolor="#42BFDD",
        color="#14080E",
        width=100,
        height=50,
        style=flet.ButtonStyle(
            shape=flet.RoundedRectangleBorder(radius=20),
        ),
        on_click=open_button_fn
    )

    dataset_tb = TextField(
        width=500,
        multiline=False,
        filled=True,
        border_width=2,
        border_radius=20,
        hint_text="Insert dataset path here or drag and drop file",
        #on_submit=send_btn_fn
    )

    # dataset row in the column
    dataset_row = Row(
        [
            dataset_tb,
            open_dataset_btn,
        ],
    )

    # dataset column
    dataset_layout = Column(
        [
            #Text("Dataset",font_family="Roboto",weight=flet.FontWeight.W_700,size=20,color=flet.colors.BLACK,text_align=flet.TextAlign.LEFT),
            Row(
                [
                    #Container(width=1),
                    Text("Dataset",font_family="Roboto",weight=flet.FontWeight.W_700,size=20,text_align=flet.TextAlign.LEFT),
                ],
            ),
            dataset_row,
        ]
    )

    # fields layout

    # select fields 
    fields_column = Column(spacing=5)
    
    fields_layout = Column(
        [
            Text("Select fields (max 3)",font_family="Roboto",weight=flet.FontWeight.W_700,size=20,text_align=flet.TextAlign.LEFT),
            fields_column,
        ],
    )

    # number of clusters layout
    number_of_clusters_txtb = TextField(
        width=500,
        multiline=False,
        filled=True,
        border_width=2,
        border_radius=20,
        hint_text="Insert number of clusters",
        #on_submit=send_btn_fn
        on_change=on_num_clusters_change,
    )

    num_of_clusters_layout = Column(
        [
            Text("Number of clusters",font_family="Roboto",weight=flet.FontWeight.W_700,size=20,text_align=flet.TextAlign.LEFT),
            number_of_clusters_txtb,
        ],
    )

    # type of centroids layout
    radio_group = RadioGroup(
        content=Row(
            [
                Radio(value=1, label="Self-select"),
                Radio(value=2, label="Auto-select"),
            ],
        ),
        on_change=radio_group_change,
    )

    # initial value for radio group
    radio_group.value = 2

    type_of_centroids_layout = Column(
        [
            Text("Type of centroids",font_family="Roboto",weight=flet.FontWeight.W_700,size=20,text_align=flet.TextAlign.LEFT),
            radio_group,
        ],
    )

    # Coordinates input layout

    coordinates_column = Column(
        [
            Text("Coordinates",font_family="Roboto",weight=flet.FontWeight.W_700,size=20,text_align=flet.TextAlign.LEFT),
            Container(height=5),
        ],
        scroll=True,
    )

    coordinates_layout = Container(
        content=coordinates_column,
        border=flet.border.all(width=2,color="#14080E"),
        border_radius=20,
        width=700,
        height=250,
        padding=15,
    )

    # initial state for coordinates layout
    coordinates_layout.visible = False

    # start button
    start_btn = ElevatedButton(
        text="Start",
        bgcolor="#6CAE75",
        color="#14080E",
        width=900,
        height=50,
        style=flet.ButtonStyle(
            shape=flet.RoundedRectangleBorder(radius=20),
        ),
        on_click=start_btn_fn
    )
    
    # resulte layout
    ch_index_label = Text("...",font_family="Roboto",weight=flet.FontWeight.W_600,size=25,text_align=flet.TextAlign.LEFT)
    centers_label = Text("...",font_family="Roboto",weight=flet.FontWeight.W_500,size=20,text_align=flet.TextAlign.LEFT)
    clusters_label = Text("...",font_family="Roboto",weight=flet.FontWeight.W_500,size=20,text_align=flet.TextAlign.LEFT)

    return_btn = ElevatedButton(
        text="Return",
        bgcolor="#d95763",
        color="#14080E",
        width=900,
        height=50,
        style=flet.ButtonStyle(
            shape=flet.RoundedRectangleBorder(radius=20),
        ),
        on_click=return_btn_fn
    )

    show_graph_btn = ElevatedButton(
        text="Show Graph",
        bgcolor="#639bff",
        color="#14080E",
        width=900,
        height=50,
        style=flet.ButtonStyle(
            shape=flet.RoundedRectangleBorder(radius=20),
        ),
        on_click=show_graph_btn_fn
    )

    result_btn_sub_layout = Column(
        [
            show_graph_btn,
            return_btn
        ],
        alignment=flet.alignment.center,
        horizontal_alignment=flet.CrossAxisAlignment.CENTER,
    )

    graph_webview = WebView(
        url="",
        expand=True,
    )

    result_layout = Column(
        [
            Text("Result",font_family="Roboto",weight=flet.FontWeight.W_700,size=20,text_align=flet.TextAlign.LEFT),
            Container(height=10),
            ch_index_label,
            Container(
                bgcolor=flet.colors.GREY_400,
                height=1,
            ),
            centers_label,
            clusters_label,
            Container(height=90),
            Row(
                [
                    Container(width=50),
                    result_btn_sub_layout
                ]
            ),
        ]
    )

    # initial state for result layout
    result_layout.visible = False

    # input section layout
    input_section_layout = Column(
        [
            dataset_layout,
            Container(height=10),
            fields_layout,
            Container(height=5),
            num_of_clusters_layout,
            type_of_centroids_layout,
            Container(height=5),
            coordinates_layout,
            Container(height=10),
            start_btn,
        ],
    )

    # main layout
    main_column = Column(
        [
            input_section_layout,
            Container(height=5),
            result_layout
        ],
        expand=True,
        alignment=flet.MainAxisAlignment.CENTER,
    )

    # bottom sheet placeholder
    bottom_sheet = BottomSheet(
        content=Column([]),
    )

    # file picker definition
    file_picker = flet.FilePicker(on_result=dataset_picked)

    # append to page
    page.overlay.append(bottom_sheet)
    page.overlay.append(file_picker)

    # render
    page.add(main_column)


flet.app(
    target=main,
    #assets_dir="assets",
)
