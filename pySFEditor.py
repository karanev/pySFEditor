### Text/Code Editor using Tkinter
### TODO:
###       2) Syntax highlighting, AutoComplete,...
###       4) File browser
###       5) On changing tabs it must be able to focus on that line again

import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
import os
import sys

import extraWidgets

class Editor(tk.Frame):
    def __init__(self, root, *args, **kwargs):
        # Unable to understand why self is necessary as first argument
        tk.Frame.__init__(self, root, *args, **kwargs)
        self.root = root
        self.__filename = None
        self.__saved = tk.BooleanVar()
        self.__modified = tk.BooleanVar()
        self.build_editor()
        self.build_context_menu()
        root.bind_class("Text", "<Control-A>", self.select_all)
        root.bind_class("Text", "<Control-a>", self.select_all)
        self.config_tags()

    def build_editor(self):
        """Builds the Editor -> Line based custom scrolled text editor"""
        self.textpad = extraWidgets.LineBasedEditor(self)
        self.linenumbers = extraWidgets.TextLineNumbers(self, width=25)
        self.linenumbers.attach(self.textpad)
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.textpad.yview)
        
        self.textpad.configure(yscrollcommand=self.vsb.set)
        self.textpad.bind("<<Change>>", self._on_change)
        self.textpad.bind("<Configure>", self._on_change)

        self.vsb.pack(side="right", fill="y")
        self.linenumbers.pack(side="left", fill="y")
        self.textpad.pack(expand=tk.YES, fill=tk.BOTH)
        self.textpad.focus_set()
    
    def _on_change(self, event=None):
        self.linenumbers.redraw()

    def cmenupopup(self, event):
        self.contextmenu.tk_popup(event.x_root, event.y_root)

    def build_context_menu(self):
        self.contextmenu = tk.Menu(self, tearoff=0)
        self.contextmenu.add_command(label="Cut", accelerator="Ctrl+X",
                command=lambda: self.textpad.event_generate("<<Cut>>"))
        self.contextmenu.add_command(label="Copy",  accelerator="Ctrl+C",
                command=lambda: self.textpad.event_generate("<<Copy>>"))
        self.contextmenu.add_command(label="Paste", accelerator="Ctrl+V",
                command=lambda: self.textpad.event_generate("<<Paste>>"))
        self.contextmenu.add_separator()
        self.contextmenu.add_command(label="Select All", accelerator="Ctrl+A",
                command=self.select_all)
        self.textpad.bind("<Button-3>", self.cmenupopup)

    def set_text_content(self, newcontent):
        """Replace the text content with new content"""
        self.textpad.delete("1.0", "end")
        self.textpad.insert("1.0", newcontent)

    def get_text_content(self):
        """Get the text content"""
        return self.textpad.get("1.0", "end")

    def set_saved(self, state):
        """Set the saved state"""
        self.__saved.set(state)

    def get_saved(self):
        """Get the saved state"""
        return self.__saved.get()

    def set_modified(self, state):
        """Set the modified state"""
        self.__modified.set(state)

    def get_modified(self):
        """Get the modified state"""
        return self.__modified.get()

    def set_filename(self, name):
        """Set the filename"""
        self.__filename = name

    def get_filename(self):
        """Get filename"""
        return self.__filename

    def select_all(self, event=None):#Don't know why event as argument is required
        """Select all the text content"""
        self.textpad.tag_add("sel", "1.0", "end-1c")

    def has_content(self):
        """Returns True/False if text has content"""
        return (True if (len(get_text_content()) > 1) else False)

    def search_for(self, query, caseinsensitive):
        self.textpad.tag_remove("match", "1.0", "end")
        count = 0
        if query:
            pos = "1.0"
            while True:
                pos = self.textpad.search(query, pos, nocase=caseinsensitive,
                        stopindex=tk.END)
                if not pos:
                    break
                lastpos = pos + '+' + str(len(query)) + 'c'
                self.textpad.tag_add("match", pos, lastpos)
                count += 1
                pos = lastpos
        return count

    def replace_for(self, replace, replacewith, caseinsensitive):
        self.textpad.tag_remove("match", "1.0", "end")
        count = 0
        if replace:
            pos ="1.0"
            while True:
                pos = self.textpad.search(replace, pos, nocase=caseinsensitive,
                        stopindex=tk.END)
                if not pos:
                    break
                lastpos = pos + '+' + str(len(replace)) + 'c'
                self.textpad.delete(pos, lastpos)
                self.textpad.insert(pos, replacewith)
                count += 1
                pos = lastpos
        return count

    def config_tags(self):
        self.textpad.tag_config("Highlight", background="#D1D4D1")
        self.textpad.tag_config("match", foreground="red", background="yellow")

class EditorMainWindow(tk.Frame):
    #binding is working with self.root.bind
    def __init__(self, root, *args, **kwargs):
        tk.Frame.__init__(self, root, *args, **kwargs)
        self.root = root
        self.opentabs = []
        self.openfiles = {}
        self.editornotebook = extraWidgets.CustomNotebook(self)
        self.editornotebook.enable_traversal()
        self.add_new_tab()
        ## Creating Icons for Menu Bar
        # File Menu Icons
        self.newicon = tk.PhotoImage(file="icons/new_file.gif")
        self.openicon = tk.PhotoImage(file="icons/open_file.gif")
        self.saveicon = tk.PhotoImage(file="icons/save_file.gif")
        # Edit Menu Icons
        self.cuticon = tk.PhotoImage(file="icons/cut.gif")
        self.copyicon = tk.PhotoImage(file="icons/copy.gif")
        self.pasteicon = tk.PhotoImage(file="icons/paste.gif")
        self.undoicon = tk.PhotoImage(file="icons/undo.gif")
        self.redoicon = tk.PhotoImage(file="icons/redo.gif")
        self.build_menubar()
        self.editornotebook.bind('<<NotebookTabChanged>>', self.__on_tab_change)
        self.editornotebook.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)
        self.build_infobar()

    def build_menubar(self):
        """Build menubar on startup and associate its bindings"""
        ## Creating Menu Bar
        self.menubar = tk.Menu(self)
        # Building File Menu ->new, open, save, save as and exit
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="New", accelerator="Ctrl+N",
                compound="left", image=self.newicon, underline=0,
                command=self.add_new_tab)
        self.root.bind("<Control-Key-n>", self.add_new_tab)
        self.filemenu.add_command(label="Open", accelerator="Ctrl+O",
                compound="left", image=self.openicon, underline=0, command=self.open_file)
        self.root.bind("<Control-Key-o>", self.open_file)
        self.filemenu.add_command(label="Save", accelerator="Ctrl+S",
                compound="left", image=self.saveicon, underline=0, command=self.save_file)
        self.root.bind("<Control-Key-s>", self.save_file)
        self.filemenu.add_command(label="Save As", accelerator="Ctrl+Shift+S",
                command=self.save_as)
        self.root.bind("<Shift-Control-Key-S>", self.save_as)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", accelerator="Alt+F4",
                command=lambda: self.root.destroy())
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        # Building Edit Menu ->undo, redo, cut, copy, paste, find and select all
        # And Making the Edit Menu work
        self.editmenu = tk.Menu(self.menubar, tearoff=0)
        self.editmenu.add_command(label="Undo", compound="left", image=self.undoicon,
                accelerator="Ctrl+Z", command=lambda: self.generate_event("Undo"))
        self.editmenu.add_command(label="Redo", compound="left", image=self.redoicon,
                accelerator="Ctrl+Y", command=lambda: self.generate_event("Redo"))
        self.editmenu.add_separator()
        self.editmenu.add_command(label="Cut", compound="left", image=self.cuticon,
                accelerator="Ctrl+X", command=lambda: self.generate_event("Cut"))
        self.editmenu.add_command(label="Copy", compound="left", image=self.copyicon,
                accelerator="Ctrl+C", command=lambda: self.generate_event("Copy"))
        self.editmenu.add_command(label="Paste", compound="left",
                image=self.pasteicon, accelerator="Ctrl+V",
                command=lambda: self.generate_event("Paste"))
        self.editmenu.add_separator()
        self.editmenu.add_command(label="Find", underline= 0,
                accelerator="Ctrl+F", command=self.find_text)
        self.root.bind("<Control-Key-f>", self.find_text)
        self.editmenu.add_command(label="Replace", underline=0, accelerator="Ctrl+H",
                command=self.replace_text)
        self.root.bind("<Control-Key-h>", self.replace_text)
        self.editmenu.add_separator()
        self.editmenu.add_command(label="Select All", underline=7,
                accelerator="Ctrl+A",
                command=self.select_all)
        self.root.bind("<Control-Key-a>", self.select_all)
        self.menubar.add_cascade(label="Edit", menu=self.editmenu)
        # Buidling View Menu ->showlnnum, showinfobar, hltcurln and themes
        self.viewmenu = tk.Menu(self.menubar, tearoff=0)
        self.__showlnnum = tk.IntVar()
        self.__showlnnum.set(1)
        self.viewmenu.add_checkbutton(label="Show Line Number",
                variable=self.__showlnnum, command=self.toggle_lnnum)
        self.__showinfobar = tk.IntVar()
        self.__showinfobar.set(1)
        self.viewmenu.add_checkbutton(label="Show Info Bar at Bottom",
                variable=self.__showinfobar, onvalue=1, offvalue=0,
                command=self.toggle_infobar)
        self.__hltcurln = tk.IntVar()
        self.__hltcurln.set(0)
        self.viewmenu.add_checkbutton(label="Highlight Current Line",
                variable=self.__hltcurln, onvalue=1, offvalue=0,
                command=self.toggle_highlight)
        self.themesmenu = tk.Menu(self.viewmenu, tearoff=0)
        self.viewmenu.add_cascade(label="Themes", menu=self.themesmenu)
        # Themes
        self.__themes = {
        "1. Default White": "000000.FFFFFF.D1D4D1",
        "2. Greygarious Grey":"83406A.D1D4D1.D1D4D1",
        "3. Lovely Lavender":"202B4B.E1E1FF.D1D4D1",
        "4. Aquamarine": "5B8340.D1E7E0.D1D4D1",
        "5. Bold Beige": "4B4620.FFF0E1.D1D4D1",
        "6. Cobalt Blue":"ffffBB.3333AA.D1D4D1",
        "7. Olive Green": "D1E7E0.5B8340.D1D4D1",
        }
        self.__themechoice = tk.StringVar()
        self.__themechoice.set("1. Default White")
        for name in sorted(self.__themes):
            ### Can implement the value arg
            self.themesmenu.add_radiobutton(label=name, variable=self.__themechoice,
                    command=self.theme)
        self.menubar.add_cascade(label="View", menu=self.viewmenu)
        # Building Help Menu -> About App and help
        self.helpmenu = tk.Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="Help")
        self.helpmenu.add_command(label="About the App")
        self.menubar.add_cascade(label="Help", menu=self.helpmenu)
        self.root.config(menu=self.menubar)

    def build_infobar(self):
        self.infobar = tk.Frame(self, height=20, bg="#dfdfdf")
        self.infobar.pack(side="bottom", fill=tk.X)
        # Line, Column Setup and Updation
        #ttk.Sizegrip(self.infobar).pack(side="right") because it produces a lag
        self.__lncolumn = tk.Label(self.infobar, text="Row 1, Column 1")
        self.__lncolumn.pack(side="right")
        #currenteditor = self.get_current_editor()
        self.lncolumn_update()

    def generate_event(self, name):
        currenteditor = self.get_current_editor()
        currenteditor.textpad.event_generate("<<{}>>".format(name))

    def select_all(self, event=None):
        currenteditor = self.get_current_editor()
        currenteditor.select_all()

    def lncolumn_update(self):
        currenteditor = self.get_current_editor()
        self.__ln, self.__column = currenteditor.textpad.index("insert").split(".")
        self.__lncolumn["text"] = "Row {}, Column {}".format(self.__ln,
                str(int(self.__column)+1))
        currenteditor.textpad.after(50, self.lncolumn_update)

    def toggle_infobar(self):
        if not (self.__showinfobar.get()):
            self.infobar.pack_forget()
        else:
            self.infobar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def toggle_lnnum(self):
        pass

    def highlight(self, editor):
        if (self.__hltcurln.get()):
            editor.textpad.tag_remove("Highlight", "1.0", "end")
            editor.textpad.tag_add("Highlight", "insert linestart", "insert lineend +1c")
        editor.textpad.after(50, lambda:self.highlight(editor))
    def undo_highlight(self, editor):
        editor.textpad.tag_remove("Highlight", "1.0", "end")
    def toggle_highlight(self, event=None):
        currenteditor = self.get_current_editor()
        self.highlight(currenteditor) if self.__hltcurln.get() else self.undo_highlight(currenteditor)

    def add_new_tab(self, event=None, filename=None):
        newTab = tk.Frame(self.editornotebook)
        newTab.editor = Editor(newTab)
        self.opentabs.append(newTab)
        if not filename:
            newTab.editor.set_filename("Untitled")
        else:
            try:
                contents = ""
                with open(filename, 'r') as f:
                    contents += f.read()
            except:
                messagebox.showerror("Could not read file!")
            newTab.editor.set_filename(filename)
            newTab.editor.set_saved(True)
            newTab.editor.set_text_content(contents)
            newTab.editor.set_modified(False)

        newTab.editor.pack(fill="both", expand=True)
        self.editornotebook.add(newTab, sticky="NSEW")
        self.editornotebook.tab(newTab, text=os.path.basename(newTab.editor.get_filename()))
        self.select_tab(newTab)

    def open_file(self, event=None):
        filenameopen = filedialog.askopenfilename(defaultextension=".txt",
                filetypes=[("All Files","*.*"),("Text Documents","*.txt")])
        # filedialog.askopenfilename() -> "" if no file is selected
        if filenameopen != "":
            self.add_new_tab(filename = filenameopen)

    def save_file(self, event=None):
        currenteditor = self.get_current_editor()
        if not currenteditor.get_saved():
            self.save_as()
        else:
            with open(currenteditor.get_filename(), 'w') as f:
                f.write(currenteditor.get_text_content().rstrip())
            currenteditor.set_modified(False)

    def save_as(self, event=None):
        currenteditor = self.get_current_editor()
        filename = filedialog.asksaveasfilename(initialfile="Untitled.txt",
                defaultextension=".txt", filetypes=[("All Files","*.*"),\
                ("Text Documents","*.txt")])
        if not filename:
            return False
        currenteditor.set_filename(filename)
        currenteditor.set_saved(True)
        self.editornotebook.tab(currenteditor, text=filename)
        with open(currenteditor.get_filename(), 'w') as f:
            f.write(currenteditor.get_text_content().rstrip())
        currenteditor.set_modified(False)
        return True

    def select_tab(self, tab=None):
        return self.editornotebook.select(tab)

    def get_current_tab(self):
        """
            Grab the current focused editor instance.
        """
        return self.opentabs[self.editornotebook.index(self.select_tab())] if self.opentabs else None

    def get_current_editor(self):
        current_tab = self.get_current_tab()
        return current_tab.editor

    def __on_tab_change(self, event=None):
        try:#in my opinion none of exception handling will be needed in this fn
            currenteditor = self.get_current_editor()
            if not currenteditor:
                sys.stderr.write("__on_tab_change called without an open editor"
                        )
            self.root.title(currenteditor.get_filename())# Omitted wm method
        except:
            sys.stderr.write("There is no editor selected :(")

    def find_text(self, event=None):
        currenteditor = self.get_current_editor()
        extraWidgets.TextFindWidget(self.root, currenteditor)

    def replace_text(self, event=None):
        currenteditor = self.get_current_editor()
        extraWidgets.TextReplaceWidget(self.root, currenteditor)

    def theme(self, event=None):
        currenteditor = self.get_current_editor()
        self.__themestring = self.__themes.get(self.__themechoice.get())
        fgc, bgc, hlt = self.__themestring.split(".")
        fgc, bgc, hlt = "#" + fgc, "#" + bgc, "#" + hlt
        currenteditor.textpad.tag_config("Highlight", background=hlt)
        currenteditor.textpad.config(fg=fgc, bg=bgc)

def main():
    root = tk.Tk()
    app = EditorMainWindow(root)
    app.pack(expand=tk.YES, fill=tk.BOTH)
    root.mainloop()

if __name__ == "__main__":
    main()
