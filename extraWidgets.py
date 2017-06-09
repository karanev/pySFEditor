### TODO: 1) Pressing enter must start search

import tkinter as tk
import tkinter.ttk as ttk
import os

class TextFindWidget(tk.Toplevel):
    def __init__(self, root, editor, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.root = root
        self.editor = editor
        self.title("Find:")
        self.transient(root)
        self.geometry("262x55+200+250")
        tk.Label(self, text="Find All:").grid(row=0, column=0, padx=1, pady=2, sticky='e')
        self.__query = tk.StringVar()
        self.__searchbar = tk.Entry(self, width=25, textvariable=self.__query)
        self.__searchbar.grid(row=0, column=1)
        self.__searchbar.focus_set()
        self.__caseinsensitive = tk.IntVar()
        tk.Checkbutton(self, text="Ignore Case", variable=self.__caseinsensitive).grid(
                row=1, column=1, sticky='e')
        tk.Button(self, text="Find All", underline=0, command=lambda: self.search(self.__query.get(),
                self.__caseinsensitive.get())).grid(row=0, column=2, padx=3, pady=2)
        self.protocol("WM_DELETE_WINDOW", self.close_find)
        #self.root.bind("<<Enter>>", self.search)

    def search(self, query, caseinsensitive):
        count = self.editor.search_for(query, caseinsensitive)
        self.__searchbar.focus_set()
        self.title("{} matches found".format(count))

    def close_find(self):
        self.editor.textpad.tag_remove("match", "1.0", "end")
        self.destroy()

class TextReplaceWidget(tk.Toplevel):
    def __init__(self, root, editor, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.root = root
        self.editor = editor
        self.title("Replace:")
        self.transient(root)
        self.geometry("307x85+200+250")
        tk.Label(self, text="Replace:").grid(row=0, column=0, padx=1, pady=2, sticky='e')
        self.__replace = tk.StringVar()
        self.__replacebar = tk.Entry(self, width=25, textvariable=self.__replace)
        self.__replacebar.grid(row=0, column=1)
        self.__replacebar.focus_set()
        tk.Label(self, text="Replace with:").grid(row=1, column=0, padx=1, pady=2, sticky='e')
        self.__replacewith = tk.StringVar()
        self.__replacewithbar = tk.Entry(self, width=25, textvariable=self.__replacewith)
        self.__replacewithbar.grid(row=1, column=1)
        self.__caseinsensitive = tk.IntVar()
        tk.Checkbutton(self, text="Ignore Case", variable=self.__caseinsensitive).grid(
                row=2, column=1, sticky='e')
        tk.Button(self, text="Find All", underline=0, command=lambda:self.editor.search_for(self.__replace.get(),
                self.__caseinsensitive.get())).grid(row=0, column=2, padx=3, pady=2, sticky="nsew")
        tk.Button(self, text="Replace All", underline=0, command=lambda: self.replace(self.__replace.get(),
                self.__replacewith.get(), self.__caseinsensitive.get())).grid(row=1, column=2, padx=3, pady=2)
        self.protocol("WM_DELETE_WINDOW", self.close_replace)
        #self.root.bind("<<Enter>>", self.search)

    def replace(self, replace, replacewith, caseinsensitive):
        count = self.editor.replace_for(replace, replacewith, caseinsensitive)
        self.__replacebar.focus_set()
        self.title("{} replaced".format(count))

    def close_replace(self):
        self.destroy()

class LineBasedEditor(tk.Text):
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)

        # Tcl code to intercept changes to the text widget and generate an event for us
        # will generate a <<Change>> event whenever text is inserted or deleted, or when
        # the view is scrolled
        self.tk.eval('''
            proc widget_proxy {widget widget_command args} {

                # call the real tk widget command with the real args
                set result [uplevel [linsert $args 0 $widget_command]]

                # generate the event for certain types of commands
                if {([lindex $args 0] in {insert replace delete}) ||
                    ([lrange $args 0 2] == {mark set insert}) || 
                    ([lrange $args 0 1] == {xview moveto}) ||
                    ([lrange $args 0 1] == {xview scroll}) ||
                    ([lrange $args 0 1] == {yview moveto}) ||
                    ([lrange $args 0 1] == {yview scroll})} {

                    event generate  $widget <<Change>> -when tail
                }

                # return the result from the real widget command
                return $result
            }
            ''')
        self.tk.eval('''
            rename {widget} _{widget}
            interp alias {{}} ::{widget} {{}} widget_proxy {widget} _{widget}
        '''.format(widget=str(self)))

class TextLineNumbers(tk.Canvas):
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.textwidget = None

    def attach(self, text_widget):
        self.textwidget = text_widget

    def redraw(self, *args):
        '''redraw line numbers'''
        self.delete("all")

        i = self.textwidget.index("@0,0")
        while True :
            dline= self.textwidget.dlineinfo(i)
            if dline is None: break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(2,y,anchor="nw", text=linenum)
            i = self.textwidget.index("%s+1line" % i)

### A notebook with close button
class Notebook(ttk.Notebook):
    def __init__(self, root):
        ttk.Notebook.__init__(self, root, style=style)
        self.root = root
        imgdir = os.path.join(os.path.dirname(__file__), 'img')
        i1 = tk.PhotoImage("img_close", file=os.path.join(imgdir, 'close.gif'))
        i2 = tk.PhotoImage("img_closeactive",
            file=os.path.join(imgdir, 'close_active.gif'))
        i3 = tk.PhotoImage("img_closepressed",
            file=os.path.join(imgdir, 'close_pressed.gif'))

        style = ttk.Style()

        style.element_create("close", "image", "img_close",
            ("active", "pressed", "!disabled", "img_closepressed"),
            ("active", "!disabled", "img_closeactive"), border=8, sticky='')

        style.layout("ButtonNotebook", [("ButtonNotebook.client", {"sticky": "nswe"})])
        style.layout("ButtonNotebook.Tab", [
            ("ButtonNotebook.tab", {"sticky": "nswe", "children":
                [("ButtonNotebook.padding", {"side": "top", "sticky": "nswe",
                                             "children":
                    [("ButtonNotebook.focus", {"side": "top", "sticky": "nswe",
                                               "children":
                        [("ButtonNotebook.label", {"side": "left", "sticky": ''}),
                         ("ButtonNotebook.close", {"side": "left", "sticky": ''})]
                    })]
                })]
            })]
        )
        self.root.bind_class("TNotebook", "<ButtonPress-1>", self.btn_press, True)
        self.root.bind_class("TNotebook", "<ButtonRelease-1>", self.btn_release)

    def btn_press(event):
        x, y, widget = event.x, event.y, event.widget
        elem = widget.identify(x, y)
        index = widget.index("@%d,%d" % (x, y))

        if "close" in elem:
            widget.state(['pressed'])
            widget.pressed_index = index

    def btn_release(event):
        x, y, widget = event.x, event.y, event.widget

        if not widget.instate(['pressed']):
            return

        elem =  widget.identify(x, y)
        index = widget.index("@%d,%d" % (x, y))

        if "close" in elem and widget.pressed_index == index:
            widget.forget(index)
            widget.event_generate("<<NotebookClosedTab>>")

        widget.state(["!pressed"])
        widget.pressed_index = None
