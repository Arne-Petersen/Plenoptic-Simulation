# Plenoptic-Simulation
Supplemental material to  
[Tim Michels](https://www.mip.informatik.uni-kiel.de/en/team/tim-michels-m-sc), [Arne Petersen](https://www.mip.informatik.uni-kiel.de/en/team/dr-ing-arne-petersen), [Luca Palmieri](https://www.mip.informatik.uni-kiel.de/en/team/luca-palmieri-m-sc), Reinhard Koch  
**_Simulation of Plenoptic Cameras_**  
3DTV Conference, 2018. (accepted, to appear) [Preprint](http://data.mip.informatik.uni-kiel.de:555/wwwadmin/Publica/2018/2018_Michels_Simulation%20of%20Plenoptic%20Cameras.pdf)

<center><img src="/images/preview.jpeg" alt="Rendering example for a plenoptic camera 2.0 setup" width="500" height="500"></center>

The .blend file contains a model for plenoptic cameras described in the paper and the example scene above consisting of the [Stanford bunny](http://graphics.stanford.edu/data/3Dscanrep/#bunny), a plane viewing some text and the Blender monkey. This simulation allows the rendering of plenoptic image data exhibiting the same effects as images from real Raytrix or Lytro cameras. Some rendering results and further explanations are given in this repository's [wiki](https://github.com/Arne-Petersen/Plenoptic-Simulation/wiki).

**Important:** Blender version 2.79 is needed in order to get correct results. For unknown reasons, the results of v2.76 show incorrect distortions.

**UPDATE:** We included another MLA and used frames in the material nodes to clarify their functionality. Check out the corresponding [wiki page](https://github.com/Arne-Petersen/Plenoptic-Simulation/wiki/HowTo:-Different-MLAs)!

A further, general note on the usage: Loading the .blend file should open a second Blender window. This is intended to function as a preview when modifying parameters. In order to get a good impression of the expected results without rendering the whole image you can simply change this views display/shading method to "Rendered" as shown in the image below.

<center><img src="/images/HowTo/howto_general.png" alt="Rendering Preview" width="500"></center>
<center><img src="/images/HowTo/howto_general2.png" alt="Rendering Preview" width="500"></center>


For further information contact <tmi@informatik.uni-kiel.de> or <arne.petersen@informatik.uni-kiel.de>.
