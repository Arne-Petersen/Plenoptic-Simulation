## Camera Generator Add-On for Blender >= 2.8

This add-on enables the user to simply generate conventional or plenoptic camera models which can be used to simulate real cameras more accurately.
The add-on is an extension of the supplemental material to

**[Tim Michels](https://www.mip.informatik.uni-kiel.de/en/team/tim-michels-m-sc), [Arne Petersen](https://www.mip.informatik.uni-kiel.de/en/team/dr-ing-arne-petersen), [Luca Palmieri](https://www.mip.informatik.uni-kiel.de/en/team/luca-palmieri-m-sc), [Reinhard Koch](https://www.mip.informatik.uni-kiel.de/en/team/prof.-dr.-ing.-reinhard-koch) - "Simulation of Plenoptic Cameras"** *, 3DTV Conference, 2018. DOI: 10.1109/3DTV.2018.8478432* [Preprint](http://data.mip.informatik.uni-kiel.de:555/wwwadmin/Publica/2018/2018_Michels_Simulation%20of%20Plenoptic%20Cameras.pdf)

which you can find in this repository's history. The add-on can also be found on gitlab [here](https://gitlab.com/ungetym/blender-camgen). Furthermore we have another repository dealing with the processing of images from plenoptic cameras [here](https://github.com/Arne-Petersen/PlenopticImageProcessing).

![Preview](https://raw.githubusercontent.com/Arne-Petersen/Plenoptic-Simulation/master/images/preview.jpeg "Preview")

### Requirements

+ Blender 2.80 or higher
+ Linux and Windows 10 have been tested
+ Render engine must be set to Cycles

### Installation

  1. Copy the `Blender_CamGen` folder into the Blender [add-on folder](https://docs.blender.org/manual/en/latest/advanced/blender_directory_layout.html#platform-dependent-paths) that is right for your operating system, e.g. for Blender 2.82 under Linux ~/.config/blender/2.82/scripts/addons/
  2. Open Blender and navigate to `Edit > Preferences > Add-ons`
  3. Find and activate `Generic: Camera_Generator` the list of available Add-ons. **You will need to press *refresh* in the Add-ons panel if you do not see the Camera_Generator option.**

### Usage

![Initial screen](https://raw.githubusercontent.com/Arne-Petersen/Plenoptic-Simulation/master/images/0.jpg "Initial screen")
1. After installing the add-on, the camera generator gui should appear as a submenu in the scene context as shown in green. 
For a quick preview of the camera output we recommend opening a second 3D view and switching to the camera's perspective by pressing 0 on the numpad (the preview tab is marked in blue).

![Camera created](https://raw.githubusercontent.com/Arne-Petersen/Plenoptic-Simulation/master/images/1.jpg "Camera created")
2. Select a camera from the **Objective** drop down menu and press the button **Create Camera Model**. 
A 3D model of the selected camera is created. Depending on the chosen scale, the model might be rather small so you have to zoom in to see it.
In order to get the correct preview, click into the preview tab and press 0 on the numpad again. 
Furthermore change the **Viewport Shading** to **Rendered** (marked in blue).
Since we want to check the cameras imaging abilities and tune its parameters, we set the **Focal Distance** (marked in green) to some value, e.g. 50 and press enter. 
The plugin now traces a few exemplary rays from the scene into the camera and tries to find the optimal sensor position to focus the camera to this distance.
To check the result visually, press **Create Checkerboard**, which creates a simple plane with checkerboard shader at the desired location.

![Checkerboard created](https://raw.githubusercontent.com/Arne-Petersen/Plenoptic-Simulation/master/images/2.jpg "Checkerboard created")
3. Now we turn off the microlens array by unchecking **Use MLA** and scale the sensor to fit the objective dimensions. 
In our example, the sensor is too small, so we set the sensor's width and height to 30mm (marked in green).
Furthermore we can adjust the number of checkerboard squares and its brightness by modifying the corresponding values in the **Checkerboard Material shader** marked in blue. 
If you can't see these shader nodes, you need to open a [shader editor tab](https://docs.blender.org/manual/en/latest/editors/shader_editor/index.html) and click on Checkerboard in the scene collection (top right).

![Checkerboard adjusted](https://raw.githubusercontent.com/Arne-Petersen/Plenoptic-Simulation/master/images/3.jpg "Checkerboard adjusted")
4. The result in our example looks acceptable, however, if the preview is blurry, you can adjust the sensor position by setting **Sensor-Objective Distance in mm** to a different value.

![Aperture modification](https://raw.githubusercontent.com/Arne-Petersen/Plenoptic-Simulation/master/images/4.jpg "Aperture modification")
5. We now zoom in to the preview and see that the white areas are bleeding into the dark areas. 
This is a result of the aperture being too large. 
The aperture size as well as the number of blades and the aperture rotation can be set via the plugin's gui.
Since the aperture exists as a model, you can see the effects in the 3D view (marked in blue) as well as the preview tab.
We chose to only modify the **Aperture Scale** (marked in green).

![Cam ready](https://raw.githubusercontent.com/Arne-Petersen/Plenoptic-Simulation/master/images/5.jpg "Cam ready")
6. If you are only interested in simulating a conventional camera, you are now good to go. 
Place some interesting objects in front of the camera, play around with the aperture and sensor position for different focus effects and finally hit F12 to render your image.
In order to simulate a plenoptic camera, however, we have to tune the microlens array. Accordingly, we activate it again by checking **Use MLA**.

![MLA active](https://raw.githubusercontent.com/Arne-Petersen/Plenoptic-Simulation/master/images/6.jpg "MLA active")
7. In the zoomed in preview we can now see, that the resulting image does not look a microlens image as produced by plenoptic cameras. 
The reason for this is, that a sharp microlens image is the result of a carefully chosen combination of  
i) main lens aperture scale  
ii) sensor position relative to the main lens  
iii) microlens diameter  
iv) MLA position relative to the sensor  
v) microlens focal lengths  
and our current values simply do not fit together. 
Since we are not interested in building a specific camera, we start adjusting the MLA by increasing the microlens diameter (marked in green).

![MLA improved](https://raw.githubusercontent.com/Arne-Petersen/Plenoptic-Simulation/master/images/7.jpg "MLA improved")
8. This results in separated microlens images and brings us much closer to the layout of a plenoptic camera.
Now we move the sensor towards the main lens by increasing the **Sensor-Objective Distance in mm** (marked in blue) which corresponds to a Galilean configuration and leads to the checkerboard corner being seen from multiple microlenses.
In order to get sharp microlens images we then have to adjust the MLA-sensor distance of the microlenses focal lengths (marked in green).

![MLA done](https://raw.githubusercontent.com/Arne-Petersen/Plenoptic-Simulation/master/images/8.jpg "MLA done")
9. In addition we chose to rotate the 6-blade aperture by 30 degree to use the sensor area more efficiently. 
Now you have a working plenoptic camera model!

### Additional features and notes

1. The lens data source is *Warren J. Smith - Modern Lens Design* and every lens file (located in the lenses folder) contains the radius/thickness/material/index/v-no/semi-aperture data for each lens surface. 
Furthermore, the files are named according to the following scheme  
$(general lens type) $(f-stop) $(opening angle)_$(author) $(patent number) $(page number in the aforementioned book).csv
2. Currently, only spherical lenses are supported.
3. If all materials of an objective are known, i.e. they are either listed in the cauchy_materials.csv or sellmeier_materials.csv file, the IOR of every lens can be adjusted according to the desired wavelength. 
This enables the user to render multiple images for different wavelength and combine the results in order to simulate chromatic abberations.
To change the wavelength, simply adjust the **Wavelength in nm** in the camera generator gui.
4. The glass material data was taken from [https://refractiveindex.info](https://refractiveindex.info) and can be extended by adding more materials to the mentioned csv files in the Blender_CamGen folder.
5. Apart from MLAs with hexagonal layouts we also support rectangular layouts. You can switch to this layout using the MLA type selector below the Use MLA checkbox.
6. You can adjust the number of vertices used to create the lens models by modifying the **Radial Vertices per Lens** and **Longitudinal Vertices per Lens**.
7. Camera models (including MLA, sensor position, aperture properties etc.) can be saved and loaded via the corresponding buttons.


### Contact

For further help, notes or requests contact us via <tmi@informatik.uni-kiel.de> or <arne.petersen@informatik.uni-kiel.de>
