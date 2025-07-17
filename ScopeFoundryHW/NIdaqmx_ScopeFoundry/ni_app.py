
from ScopeFoundry import BaseMicroscopeApp

class NI_App(BaseMicroscopeApp):

    # this is the name of the microscope that ScopeFoundry uses 
    # when storing data
    name = 'ni_app'
    
    # You must define a setup function that adds all the 
    #capablities of the microscope and sets default settings
    def setup(self):
        
        #Add App wide settings
        
        #Add hardware components
        print("Adding Hardware Components")
        from ni_ao_hardware import NI_AO_hw
        from ni_do_hardware import NI_DO_hw
        from ni_co_hardware import NI_CO_hw
        self.add_hardware(NI_AO_hw(self))
        self.add_hardware(NI_DO_hw(self))
        self.add_hardware(NI_CO_hw(self))
        
        #Add measurement components
        print("Create Measurement objects")
        # Connect to custom gui
        
        # load side panel UI
        
        # show ui
        self.ui.show()
        self.ui.activateWindow()


if __name__ == '__main__':
    import sys
    
    app = NI_App(sys.argv)
    sys.exit(app.exec_())