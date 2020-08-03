from ScopeFoundry import BaseMicroscopeApp


class FakeCameraApp(BaseMicroscopeApp):
    
    name = 'FakeCameraApp'
    
    def setup(self):
        
        from FakeCameraHardware import FakeCameraHardware
        self.add_hardware(FakeCameraHardware(self))
        print("Adding Hardware Components")
        
        from FakeCameraMeasurement import FakeCameraMeasurement
        self.add_measurement(FakeCameraMeasurement(self))
        print("Adding measurement components")
        
        self.ui.show()
        self.ui.activateWindow()
    
if __name__ == '__main__':
            
    import sys
    app = FakeCameraApp(sys.argv)
    
    
    ################### for debugging only ##############
    app.settings_load_ini(".\\settings\\settings0.ini")
    for hc_name, hc in app.hardware.items():
        hc.settings['connected'] = True
    #####################################################    
        
    sys.exit(app.exec_())