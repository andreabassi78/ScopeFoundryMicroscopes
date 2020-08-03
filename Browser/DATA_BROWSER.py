from __future__ import absolute_import, print_function
from ScopeFoundry.data_browser import DataBrowser
import logging

#try:
#    import FoundryDataBrowser.viewers as viewers
#except:
#    import viewers
    
import sys

app = DataBrowser(sys.argv)

#app.logging_widget.show()

# views are loaded in order of more generic to more specific.
## ie the last loaded views are checked first for compatibility
   
try:
    from viewers.image_stack_H5_view import ImageStackH5
    app.load_view(ImageStackH5(app))
except ImportError:
    logging.warning("Error loading ImageStackH5 viewer")

# try:    
#     from viewers.thorlabsPD_H5_view import PlotH5
#     app.load_view(PlotH5(app))
# except ImportError:
#     logging.warning("Error loading PlotH5 viewer")    
    

from viewers.h5_tree import H5TreeView, H5TreeSearchView
app.load_view(H5TreeView(app))
app.load_view(H5TreeSearchView(app))

sys.exit(app.exec_())