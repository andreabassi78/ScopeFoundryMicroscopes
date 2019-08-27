from setuptools import setup

setup(
    name = 'ScopeFoundryHW.virtual_function_gen',
    
    version = '0.0.1',
    
    description = 'ScopeFoundry Hardware plug-in: Virtual function generator',
    
    # Author details
    author='Edward S. Barnard',
    author_email='esbarnard@lbl.gov',

    # Choose your license
    license='BSD',

    package_dir={'ScopeFoundryHW.virtual_function_gen': '.'},
    
    packages=['ScopeFoundryHW.virtual_function_gen',],
        
    package_data={
        '':["README*", 'LICENSE', # include License and readme 
            "*.ui", # include QT ui files 
            ], 
        },
    )
