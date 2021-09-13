"""
deformation module

Module for saving and loading skin weights using ngSkinTools
"""
import os

import pymel.core as pm
try:
    from ngSkinTools.mllInterface import MllInterface
    from ngSkinTools.importExport import LayerData, JsonExporter, JsonImporter
except:
    pass
import json

def save_weights(weight_dir, geo_list=[]):
    """
    save geometry weights for character
    """
    print( weight_dir)

    for obj in geo_list:
        # save dir and save file

        weight_file = os.path.join(weight_dir, obj + '.json')
        obj_shape = pm.PyNode(obj).getChildren(type='shape')[0]

        layerData = LayerData()
        try:
            layerData.loadFrom(obj_shape.name())
        except Exception as e:
            pm.warning(str(e))
            try:
                mll = MllInterface()
                mll.setCurrentMesh(obj_shape.name())
                ass = mll.initLayers()
                layer = mll.createLayer('Base Weights')
            except:
                raise
        exporter = JsonExporter()
        jsonContents = exporter.process(layerData)
        # string "jsonContents" can now be saved to an external file

        with open(weight_file, 'w') as f:
            f.write(jsonContents)
            #json.dump(jsonContents, f)
        # save skin weight file

        #mc.select(obj)
        #bSkinSaver2.bSaveSkinValues(weight_file)

        print ("Saved to: " + weight_file)
        pm.select(None)


def load_weights(weight_dir, geo_list=[], joint_list=[]):
    """
    load geometry weights for character
    """

    # weights folder

    weight_files = os.listdir(weight_dir)
    if weight_files:

        # load skin weights
        # alternatively, if you don't want such a long line of code:

        for geo in geo_list:
            kwargs = {
                'toSelectedBones': True,
                'bindMethod': 0,
                'skinMethod': 2,
                'name': geo.replace('geo', 'scls'),
                'normalizeWeights': 1,
                'maximumInfluences': 4
            }
            try:
                scls = pm.skinCluster(joint_list, geo, **kwargs)[0]
            except RuntimeError:
                print ('bad bind' + str(RuntimeError))

        for wt_file in weight_files:

            ext_res = os.path.splitext(wt_file)

            # check extension format
            if not ext_res > 1:
                continue

            # check skin weight file
            if not ext_res[1] == '.json':
                continue

            # check geometry list
            if geo_list and not ext_res[0] in geo_list:
                continue

            # check if objects exist
            if not pm.objExists(ext_res[0]):
                continue

            fullpath_weight_file = os.path.join(weight_dir, wt_file)

            if ".json" in ext_res[1]:
                with open(fullpath_weight_file, 'r') as f:
                    data = f.read()

                #with open(fullpath_weight_file) as json_file:
                    #data = json.load(json_file)
                importer = JsonImporter()
                layerData = importer.process(data)
                try:
                    layerData.saveTo(wt_file.replace('.json', 'Shape'))
                except Exception as e:
                    print ('warning:' + str(e))

            #bSkinSaver2.bLoadSkinValues(loadOnSelection=False, inputFile=fullpath_weight_file)
    else:
        pm.warning('No skin weight files in directory!')