
import os
import datetime

import numpy as np
import Ngl
from PIL import Image

import sys
current_path = sys.path[0]
ex_op_str = current_path[current_path.index('progs')+6: current_path.index('w2w_ensembleplots')-1]
sys.path.append('/progs/{}'.format(ex_op_str))
from w2w_ensembleplots.core.read_data import read_forecast_data, read_grid_coordinates
from w2w_ensembleplots.core.download_forecast import get_timeshift
from w2w_ensembleplots.core.gridpoint_order import cut_by_domain


def det_contourplot(domains, variable1, variable2, model, run, plot_type):

    if plot_type == 'map_deterministic_overview':
        hours = list(range(0, 180+1, 12))
    elif plot_type == 'map_hurricane':
        hours = list(range(0, 180+1, 6))

    var1var2 = variable1['name'] + '_' + variable2['name']


    # define paths #

    ex_op_str = current_path[current_path.index('progs')+6: current_path.index('w2w_ensembleplots')-1]
    # ex_op_str equals either 'experimental' or 'operational' depending on where this script is

    path = dict(base = '/')
    if plot_type == 'map_deterministic_overview':
        path['plots'] = 'data/plots/{}/map_deterministic_overview/'.format(ex_op_str)
    elif plot_type == 'map_hurricane':
        path['plots'] = 'data/plots/{}/map_hurricane/'.format(ex_op_str)

    subfolder = 'run_{:4d}{:02d}{:02d}{:02d}'.format(run['year'], run['month'], run['day'], run['hour'])

    filename_latest_run = 'latest_run_det_overview_map_{}.txt'.format(var1var2)
    with open(path['base'] + path['plots'] + filename_latest_run, 'w') as file:
        file.write(subfolder[4:])

    if not os.path.isdir(path['base'] + path['plots'] + subfolder):
        os.makedirs(path['base'] + path['plots'] + subfolder)
    path['plots'] += subfolder + '/' 

    if not os.path.isdir(path['base'] + path['plots'] + var1var2):
        os.makedirs(path['base'] + path['plots'] + var1var2)
    path['plots'] += var1var2 + '/'
 

    # load icosahedral grid information only once #

    clat, clon, vlat, vlon = read_grid_coordinates(model, 'icosahedral')


    # start here the whole plotting routine #

    print('plotting model: {}, run: {:02d}.{:02d}.{:4d}, {:02d}UTC, vars: {} {}'.format(
          model, run['day'], run['month'], run['year'], run['hour'],
          variable1['name'], variable2['name']))

    for hour in hours[:1]:
        print('forecast hour:', hour)

        ll_lat, ll_lon = read_grid_coordinates(model, 'latlon_0.25')
        data_array1 = read_forecast_data(model, variable1['grid'], run, variable1['name'], fcst_hour=hour)

        data_array2f = read_forecast_data(model, variable2['grid'], run, variable2['name'], fcst_hour=hour)
        if variable2['grid'] == 'latlon_0.25':
            data_array2, ll_lon = Ngl.add_cyclic(data_array2f, ll_lon)


        for domain in domains:
            print('domain:', domain['name'])

            if domain['limits_type'] == 'radius':
                margin_deg = 20
            elif domain['limits_type'] == 'deltalatlon' or domain['limits_type'] == 'angle':
                margin_deg = 20

            data_array1_cut, clat_cut, clon_cut, vlat_cut, vlon_cut = cut_by_domain(domain, 'icosahedral',
                                                                                    data_array1, clat, clon, vlat, vlon,
                                                                                    margin_deg)

            # example plot_name: icon-global-det_2020070512_prec_rate_mslp_europe_000h.png
            plot_name = '{}_{:4d}{:02d}{:02d}{:02d}_{}_{}_{}_{:03d}h'.format(
                         model, run['year'], run['month'], run['day'], run['hour'],
                         variable1['name'], variable2['name'], domain['name'], hour)



            # plot basic map with borders #

            wks_res             = Ngl.Resources()
            if domain['limits_type'] == 'radius' or domain['limits_type'] == 'angle':
                x_resolution        = 800
                y_resolution        = 800
            elif domain['limits_type'] == 'deltalatlon':
                x_resolution        = 1200
                y_resolution        = 1200
            wks_res.wkWidth     = x_resolution
            wks_res.wkHeight    = y_resolution

            if variable1['name'] == 'prec_rate':
                wks_res.wkColorMap = 'precip3_16lev'
                levels1 = ([0.1,0.2,0.5,1,2,5,10,20,50])
            if variable1['name'] == 'prec_6h':
                wks_res.wkColorMap = 'precip3_16lev'
                levels1 = ([0.1,0.2,0.5,1,2,5,10,20,50])
            elif variable1['name'] == 't_850hPa':
                wks_res.wkColorMap = 'BkBlAqGrYeOrReViWh200'
                levels1 = np.arange(-40,40,4)
            elif variable1['name'] == 'wind_300hPa':
                wks_res.wkColorMap = 'wh-bl-gr-ye-re' #from 100 to 200
                levels1 = np.arange(150,300,25) # irgendwie so machen dass es erst bei grün anfängt

            wks_type = 'png'
            wks = Ngl.open_wks(wks_type, path['base'] + path['plots'] + plot_name, wks_res)


            mpres   = Ngl.Resources()
            mpres.mpProjection = domain['projection']

            if domain['limits_type'] == 'radius':
                mpres.mpLimitMode  = 'LatLon'
                mpres.mpCenterLonF = domain['centerlon']
                mpres.mpCenterLatF = domain['centerlat']
                cutout_plot = dict(
                                    lat_min = float(np.where(domain['centerlat'] - domain['radius'] / 111.2 < -90,
                                                       -90, domain['centerlat'] - domain['radius'] / 111.2)),
                                    lat_max = float(np.where(domain['centerlat'] + domain['radius'] / 111.2 > 90,
                                                       90, domain['centerlat'] + domain['radius'] / 111.2)),
                                   )
                cutout_plot['lon_min'] = float(np.where(cutout_plot['lat_min'] <= -90 or cutout_plot['lat_max'] >= 90,
                                               0,
                                               domain['centerlon'] - domain['radius'] \
                                                / (111.2 * np.cos(domain['centerlat']*np.pi/180))))
                cutout_plot['lon_max'] = float(np.where(cutout_plot['lat_min'] <= -90 or cutout_plot['lat_max'] >= 90,
                                               360,
                                               domain['centerlon'] + domain['radius'] \
                                                / (111.2 * np.cos(domain['centerlat']*np.pi/180))))
                mpres.mpMinLonF     = cutout_plot['lon_min']
                mpres.mpMaxLonF     = cutout_plot['lon_max']
                mpres.mpMinLatF     = cutout_plot['lat_min']
                mpres.mpMaxLatF     = cutout_plot['lat_max']

            elif domain['limits_type'] == 'deltalatlon':
                mpres.mpLimitMode  = 'LatLon'
                mpres.mpCenterLonF = 0
                mpres.mpCenterLatF = 0
                mpres.mpMinLonF    = domain['centerlon'] - domain['deltalon_deg']
                mpres.mpMaxLonF    = domain['centerlon'] + domain['deltalon_deg']
                mpres.mpMinLatF    = domain['centerlat'] - domain['deltalat_deg']
                mpres.mpMaxLatF    = domain['centerlat'] + domain['deltalat_deg']

            elif domain['limits_type'] == 'angle':
                mpres.mpLimitMode    = 'Angles'
                mpres.mpCenterLonF   = domain['centerlon']
                mpres.mpCenterLatF   = domain['centerlat']
                mpres.mpLeftAngleF   = domain['angle']
                mpres.mpRightAngleF  = domain['angle']
                mpres.mpTopAngleF    = domain['angle']
                mpres.mpBottomAngleF = domain['angle']

            #print('domain center point lat:', domain['centerlat'])
            #print('lat_min:', cutout_plot['lat_min'])
            #print('lat_max:', cutout_plot['lat_max'])
            #print('lon_min:', cutout_plot['lon_min'])
            #print('lon_max:', cutout_plot['lon_max'])

            mpres.nglMaximize   = False
            mpres.vpXF          = 0.001
            mpres.vpYF          = 1.00
            mpres.vpWidthF      = 0.88
            mpres.vpHeightF     = 1.00
            mpres.mpMonoFillColor = 'True'
            if variable1['name'] == 't_850hPa' :
                mpres.mpFillColors = ['transparent', 'transparent', 'transparent', 'transparent']
            elif variable1['name'] == 'wind_300hPa' :
                mpres.mpFillColors = ['transparent', 'white', 'navajowhite1', 'transparent']
            elif variable1['name'] == 'prec_rate' :
                mpres.mpFillColors = ['transparent', 'transparent', 'transparent', 'transparent']

            #Ngl.set_values(wks,mpres)
            mpres.mpFillOn       = True
            #resources.cnFillDrawOrder       = 'Predraw'     # draw contours first
            mpres.mpGridAndLimbOn            = False
            mpres.mpGreatCircleLinesOn  = False

            #mpres.mpOutlineDrawOrder       = 'PreDraw'
            mpres.mpDataBaseVersion         = 'MediumRes'
            mpres.mpDataSetName             = 'Earth..4'
            if domain['name'] == 'usa':
                mpres.mpOutlineBoundarySets      = 'GeophysicalAndUSStates'
                mpres.mpProvincialLineColor      = 'black'
                mpres.mpProvincialLineThicknessF = 2. * x_resolution / 1000
            else:
                mpres.mpOutlineBoundarySets     = 'national'
            mpres.mpGeophysicalLineColor        = 'black'
            mpres.mpNationalLineColor           = 'black'
            mpres.mpGeophysicalLineThicknessF   = 2. * x_resolution / 1000
            mpres.mpNationalLineThicknessF      = 2. * x_resolution / 1000

            mpres.mpPerimOn                     = True
            mpres.mpPerimLineColor              = 'black'
            mpres.mpPerimLineThicknessF         = 8.0 * x_resolution / 1000
            mpres.tmXBOn = False
            mpres.tmXTOn = False
            mpres.tmYLOn = False
            mpres.tmYROn = False

            mpres.nglDraw        =  False              #-- don't draw plot
            mpres.nglFrame       =  False              #-- don't advance frame



            # settings for variable1 / shading #

            v1res = Ngl.Resources()
            v1res.sfDataArray       = data_array1_cut
            v1res.sfXArray          = clon_cut
            v1res.sfYArray          = clat_cut
            v1res.sfXCellBounds     = vlon_cut
            v1res.sfYCellBounds     = vlat_cut
            v1res.sfMissingValueV   = 9999

            v1res.cnLinesOn             = False   # Turn off contour lines.
            v1res.cnFillOn              = True
            v1res.cnFillMode            = 'CellFill'
            #v1res.cnFillOpacityF        = 0.5   
            #v1res.cnFillDrawOrder       = 'Predraw'
            v1res.cnLevelSelectionMode = 'ExplicitLevels' 
            v1res.cnLevels      = levels1

            v1res.lbLabelBarOn          = True
            v1res.lbAutoManage          = False
            v1res.lbOrientation         = 'vertical'
            v1res.lbLabelOffsetF        = 0.04      # minor axis fraction: the distance between colorbar and numbers
            v1res.lbBoxMinorExtentF     = 0.20      # minor axis fraction: width of the color boxes when labelbar down
            v1res.lbTopMarginF          = 0.2      # make a little more space at top for the unit label
            v1res.lbRightMarginF        = 0.0
            if variable1['name'] == 't_850hPa' :
                v1res.lbBottomMarginF   = -0.07
            elif variable1['name'] == 'wind_300hPa' :
                v1res.lbBottomMarginF   = -0.35
            elif variable1['name'] == 'prec_rate' :
                v1res.lbBottomMarginF   = -0.2
            v1res.lbLeftMarginF         = -0.35

            v1res.cnLabelBarEndStyle    = 'ExcludeOuterBoxes'
            #if variable1['name'] == 'prec_rate' :
            #    v1res.cnLabelBarEndStyle    = 'IncludeOuterBoxes'
            #v1res.cnExplicitLabelBarLabelsOn = True
            #v1res.pmLabelBarDisplayMode =  'Always'
            v1res.pmLabelBarWidthF      = 0.10
            #v1res.lbLabelStrings        = label_str_list
            v1res.lbLabelFontHeightF    = 0.010
            #v1res.lbBoxCount            = 40
            v1res.lbBoxSeparatorLinesOn = False
            v1res.lbBoxLineThicknessF   = 4
            #v1res.lbBoxEndCapStyle     = 'TriangleBothEnds'
            v1res.lbLabelAlignment      = 'ExternalEdges'
            v1res.lbLabelStride         = 1

            v1res.nglFrame = False
            v1res.nglDraw  = False



            # settings for variable2 / contourlines #

            v2res = Ngl.Resources()
            v2res.sfDataArray       = data_array2
            v2res.sfXArray          = ll_lon
            v2res.sfYArray          = ll_lat
            v2res.sfMissingValueV   = 9999  
            #v2res.trGridType        = 'TriangularMesh'
            v2res.cnFillOn       = False
            v2res.cnLinesOn      = True
            v2res.cnLineLabelsOn = True

            v2res.cnLineLabelPlacementMode = 'Constant'
            if plot_type == 'map_hurricane':
                v2res.cnLineLabelFontHeightF = 0.008
            elif plot_type == 'map_deterministic_overview':
                v2res.cnLineLabelFontHeightF = 0.010
            v2res.cnLineDashSegLenF = 0.25
            v2res.cnLabelDrawOrder = 'PostDraw' # necessary to make everything visible
            v2res.cnInfoLabelOn = False

            v2res.cnSmoothingOn = False
            v2res.cnSmoothingDistanceF = 0.01
            v2res.cnSmoothingTensionF = 0.1
            if variable2['name'] == 'mslp':
                if plot_type == 'map_hurricane':
                    spcng = 5
                elif plot_type == 'map_deterministic_overview':
                    spcng = 5
            #levesl2 = np.arange(850,1100,5)
            elif variable2['name'] == 'gph_500hPa':
                spcng = 4
            elif variable2['name'] == 'gph_300hPa':
                spcng = 4
            v2res.cnLevelSelectionMode = 'ManualLevels' 
            v2res.cnLevelSpacingF      =  spcng
            #v2res.cnLevels = levels2
            #v2res.cnRasterSmoothingOn = True

            v2res.nglFrame = False
            v2res.nglDraw  = False


            # settings for unit text #

            text_str = variable1['unit']
            text_res_1 = Ngl.Resources()
            text_res_1.txFontColor      = 'black'
            text_res_1.txFontHeightF = 0.013
            text_x = 0.965



            # set domain specific resource settings #

            if domain['name'] == 'europe':
                v2res.cnLineThicknessF = 5.0
                v2res.cnLineLabelInterval = 1
                text_y = 0.865
            elif domain['name'] == 'europe_and_north_atlantic':
                v2res.cnLineThicknessF = 4.0
                v2res.cnLineLabelInterval = 2
                text_y = 0.83
            elif domain['name'] == 'usa':
                v2res.cnLineThicknessF = 4.0
                v2res.cnLineLabelInterval = 1
                text_y = 0.875
            elif domain['name'] == 'southern_south_america':
                v2res.cnLineThicknessF = 4.0
                v2res.cnLineLabelInterval = 2
                text_y = 0.885
            elif domain['name'] == 'north_pole' or domain['name'] == 'south_pole':
                v2res.cnLineThicknessF = 3.0
                v2res.cnLineLabelInterval = 4
                text_y = 0.93
            elif domain['name'] == 'atlantic_hurricane_basin':
                v2res.cnLineThicknessF = 3.0
                v2res.cnLineLabelInterval = 2
                text_y = 0.665
            elif domain['name'] == 'gulf_of_mexico':
                v2res.cnLineThicknessF = 3.0
                v2res.cnLineLabelInterval = 1
                text_y = 0.78
            else:
                print('no domain specific settings defined for this domain:', domain['name'])
                exit()



            # put everything together # 

            basic_map = Ngl.map(wks, mpres)
            contourshades_plot = Ngl.contour(wks, data_array1_cut, v1res)
            contourlines_plot = Ngl.contour(wks, data_array2, v2res)

            Ngl.overlay(basic_map, contourshades_plot)
            Ngl.overlay(basic_map, contourlines_plot)
     
            Ngl.draw(basic_map)
            Ngl.text_ndc(wks, text_str, text_x, text_y, text_res_1)
            Ngl.frame(wks)
            Ngl.destroy(wks)
            #Ngl.end()


            # cut top and bottom whitespace of plot #

            im = Image.open(path['base'] + path['plots'] + plot_name + '.png')
            image_array = np.asarray(im.convert('L'))
            image_array = np.where(image_array < 255, 1, 0)
            image_filter = np.amax(image_array, axis=1)
            vmargins = [np.nonzero(image_filter)[0][0], np.nonzero(image_filter[::-1])[0][0]]
            #print(vmargins)
            #print(im.size)

            im_cropped = Image.new('RGB',(im.size[0], im.size[1] - vmargins[0] - vmargins[1]), (255,255,255))
            im_cropped.paste(im.crop((0, vmargins[0], im.size[0], im.size[1] - vmargins[1])), (0, 0))
            #print(im_cropped.size)
            im.close()
            im_cropped.save(path['base'] + path['plots'] + plot_name + '.png', 'png')
            im_cropped.close()


    del data_array1, data_array1_cut, data_array2, vlat, vlon, clat, clon


    # copy all plots and .txt-file to imk-tss-web server #

    '''path_webserver = '/home/iconeps/Data3/plots/icon/deterministic_overview_maps/{}'.format(var1var2)
    os.system('scp ' + path['base'] + path['plots'] + '*.png '\
              + 'iconeps@imk-tss-web.imk-tro.kit.edu:' + path_webserver)

    path_webserver = '/home/iconeps/Data3/plots/icon/deterministic_overview_maps'
    path_latest_run_files = 'data/plots/{}/map_deterministic_overview/'.format(ex_op_str)
    os.system('scp ' + path['base'] + path_latest_run_files + filename_latest_run\
              + ' iconeps@imk-tss-web.imk-tro.kit.edu:' + path_webserver)'''

    return
