#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import gi
import subprocess
import os
import tempfile

gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
gi.require_version('Gtk', '3.0')

from gi.repository import Gimp, GimpUi, Gtk, GLib, GObject, Gio

TEXCONV_PATH = "C:/tools/texconv.exe"  # <- CHANGE TO YOUR OWN PATH!


class DDSExportPlugin(Gimp.PlugIn):
    def __init__(self):
        super().__init__()
        self.format_map = {
            "BC1 / DXT1": "BC1_UNORM",
            "BC2 / DXT3": "BC2_UNORM",
            "BC3 / DXT5": "BC3_UNORM",
            "BC4 (R)": "BC4_UNORM",
            "BC5 (RG)": "BC5_UNORM",
            "BC7 (HQ)": "BC7_UNORM",
            "R8G8B8A8 (Uncompressed)": "R8G8B8A8_UNORM"
        }

    def do_query_procedures(self):
        return ["jb-dds-export"]

    def do_set_i18n(self, name):
        return False

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name,
            Gimp.PDBProcType.PLUGIN,
            self.run, None
        )
        procedure.set_image_types("*")
        procedure.set_menu_label("Export as DDS (texconv)...")
        procedure.add_menu_path("<Image>/File/Export")
        procedure.set_documentation(
            "Export to DDS using texconv",
            "Exports the image to DDS using the external tool texconv",
            name
        )
        procedure.set_attribution("Tenir", "Tenir", "2025")
        return procedure

    def show_export_dialog(self):
        GimpUi.init("dds-export")

        dialog = Gtk.Dialog(title="Export image as DDS (texconv)", flags=0)
        dialog.set_default_size(400, 200)
        dialog.set_border_width(10)

        content = dialog.get_content_area()
        grid = Gtk.Grid(column_spacing=10, row_spacing=8)
        content.add(grid)

        format_label = Gtk.Label(label="Compression format:", xalign=0)
        self.format_combo = Gtk.ComboBoxText()
        for name in self.format_map.keys():
            self.format_combo.append_text(name)
        self.format_combo.set_active(0)
        grid.attach(format_label, 0, 0, 1, 1)
        grid.attach(self.format_combo, 1, 0, 2, 1)

        options_label = Gtk.Label(label="Options:", xalign=0)
        self.mipmap_check = Gtk.CheckButton(label="Generate mipmaps")
        self.mipmap_check.set_active(True)
        self.srgb_check = Gtk.CheckButton(label="sRGB color space (perceptual)")
        self.srgb_check.set_active(True)
        self.overwrite_check = Gtk.CheckButton(label="Overwrite existing file")
        self.overwrite_check.set_active(True)

        options_grid = Gtk.Grid(column_spacing=10, row_spacing=5)
        options_grid.attach(self.mipmap_check, 0, 0, 1, 1)
        options_grid.attach(self.srgb_check, 0, 1, 1, 1)
        options_grid.attach(self.overwrite_check, 0, 2, 1, 1)

        grid.attach(options_label, 0, 1, 1, 1)
        grid.attach(options_grid, 1, 1, 2, 1)

        dialog.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("_Export", Gtk.ResponseType.OK)
        dialog.show_all()

        result = dialog.run()
        values = None
        if result == Gtk.ResponseType.OK:
            selected_format = self.format_combo.get_active_text()
            values = {
                "format": self.format_map.get(selected_format, "BC1_UNORM"),
                "mipmap": self.mipmap_check.get_active(),
                "srgb": self.srgb_check.get_active(),
                "overwrite": self.overwrite_check.get_active()
            }
        dialog.destroy()
        return values

    def save_temp_image(self, image, filepath):
        try:
            png_proc = Gimp.get_pdb().lookup_procedure("file-png-export")
            config = png_proc.create_config()
            config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
            config.set_property("image", image)
            config.set_property("file", Gio.File.new_for_path(filepath))
            result = png_proc.run(config)
            if result.index(0) != Gimp.PDBStatusType.SUCCESS:
                msg = result.index(1).message if result.index(1) else "Unknown error"
                raise Exception(f"PNG save error: {msg}")
            return True
        except Exception as e:
            raise Exception(f"Temporary file save error: {e}")

    def run(self, procedure, run_mode, image, drawables, config, run_data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            try:
                options = self.show_export_dialog()
                if not options:
                    return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

                file_chooser = Gtk.FileChooserDialog(
                    title="Save as DDS",
                    action=Gtk.FileChooserAction.SAVE,
                    buttons=("_Cancel", Gtk.ResponseType.CANCEL, "_Save", Gtk.ResponseType.OK)
                )
                file_chooser.set_current_name("texture.dds")

                filter_dds = Gtk.FileFilter()
                filter_dds.set_name("DDS files")
                filter_dds.add_pattern("*.dds")
                file_chooser.add_filter(filter_dds)

                response = file_chooser.run()
                export_path = None
                if response == Gtk.ResponseType.OK:
                    export_path = file_chooser.get_filename()
                    if not export_path.lower().endswith(".dds"):
                        export_path += ".dds"
                file_chooser.destroy()

                if not export_path:
                    return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

                if not os.path.isfile(TEXCONV_PATH):
                    raise Exception(f"texconv.exe not found at path: {TEXCONV_PATH}")

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                    temp_png = temp_file.name

                try:
                    self.save_temp_image(image, temp_png)

                    command = [
                        TEXCONV_PATH,
                        "-f", options["format"],
                        "-y" if options["overwrite"] else "",
                        "-o", os.path.dirname(export_path),
                        "-ft", "DDS",
                        temp_png
                    ]

                    if options["mipmap"]:
                        command.extend(["-m", "0"])
                    if options["srgb"]:
                        command.append("-srgb")

                    # Remove empty args
                    command = [arg for arg in command if arg]

                    result = subprocess.run(
                        command,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                    )

                    output_dir = os.path.dirname(export_path)
                    expected_dds = os.path.splitext(os.path.basename(temp_png))[0] + ".DDS"
                    output_dds = os.path.join(output_dir, expected_dds)

                    if not os.path.isfile(output_dds):
                        raise Exception(f"texconv did not produce a file:\n{result.stderr or 'Unknown error'}")

                    os.replace(output_dds, export_path)

                    Gimp.message(f"Successfully exported to:\n{export_path}\n\n{result.stdout}")

                finally:
                    if os.path.exists(temp_png):
                        try:
                            os.remove(temp_png)
                        except:
                            pass

                return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

            except Exception as e:
                return procedure.new_return_values(
                    Gimp.PDBStatusType.EXECUTION_ERROR,
                    GLib.Error.new_literal(GLib.quark_from_string("DDS Export"), str(e), -1)
                )

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


Gimp.main(DDSExportPlugin.__gtype__, sys.argv)
