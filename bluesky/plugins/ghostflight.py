""" BlueSky plugin template. The text you put here will be visible
    in BlueSky as the description of your plugin. """
from random import randint
import numpy as np
# Import the global bluesky objects. Uncomment the ones you need
from bluesky import core, stack, traf  #, settings, navdb, sim, scr, tools

### Initialization function of your plugin. Do not change the name of this
### function, as it is the way BlueSky recognises this file as a plugin.
def init_plugin():
    ghostflight = GhostFlight()

    config = {
        'plugin_name': 'GHOSTFLIGHT',
        'plugin_type': 'sim',
    }

    return config



### Entities in BlueSky are objects that are created only once (called singleton)
### which implement some traffic or other simulation functionality.
### To define an entity that ADDS functionality to BlueSky, create a class that
### inherits from bluesky.core.Entity.
### To replace existing functionality in BlueSky, inherit from the class that
### provides the original implementation (see for example the asas/eby plugin).
class GhostFlight(core.Entity):
    ''' Example new entity object for BlueSky. '''
    def __init__(self):
        super().__init__()

        with self.settrafarrays():
            self.reported_lat = np.array([])
            self.reported_lon = np.array([])
            self.spoof_active = np.array([], dtype=bool)

            self.lat_offset = np.array([])
            self.lon_offset = np.array([])

            self.prev_reported_lat = np.array([])
            self.prev_reported_lon = np.array([])
            self.suspicion= np.array([])

    # called everytime a plane is spawned.
    def create(self, n=1):
        super().create(n)
        self.reported_lat[-n:] = traf.lat[-n:]
        self.reported_lon[-n:] = traf.lon[-n:]
        self.spoof_active[-n:] = False

        self.lat_offset[-n:] = 0.0
        self.lon_offset[-n:] = 0.0

        self.prev_reported_lat[-n:] = traf.lat[-n:]
        self.prev_reported_lon[-n:] = traf.lon[-n:]
        self.suspicion[-n:] = 0.0

    @stack.command
    def ghostpos(self, acid: 'acid'):
        return True, (
            f'{traf.id[acid]}\n'
            f'True:     {traf.lat[acid]:.5f}, {traf.lon[acid]:.5f}\n'
            f'Reported: {self.reported_lat[acid]:.5f}, '
            f'Suspicion Value: {self.suspicion[acid]:.5f}, '
            f'{self.reported_lon[acid]:.5f}'
    )

    @stack.command
    def spoof(self, acid: 'acid'):
        self.spoof_active[acid] = True
        return True, f'Spoofing started for {traf.id[acid]}'

    @core.timed_function(name='ghostflight_update', dt=1)
    def update(self):
        dt = 1
        for plane in range(len(traf.id)):
            if self.spoof_active[plane]:
                offsetvalue = randint(1,99) * 0.00001
                self.lat_offset[plane] += offsetvalue
                self.lon_offset[plane] += offsetvalue
            self.reported_lat[plane] = traf.lat[plane] + self.lat_offset[plane]
            self.reported_lon[plane] = traf.lon[plane] + self.lon_offset[plane]

            prev_lat = self.prev_reported_lat[plane]
            prev_lon = self.prev_reported_lon[plane]

            # for the sake of realism we'll pretend our trusted speed and heading values came from the aircraft's IRS directly
            irs_groundspeed = traf.gs[plane] # is in m s ^-1
            # heading
            irs_track = traf.trk[plane] # this is in degrees from 0 to 360
            distance_travelled = irs_groundspeed*dt
            track_radians = np.radians(irs_track)

            north_dist = distance_travelled * np.cos(track_radians)
            east_dist = distance_travelled * np.sin(track_radians)
            earth_radius = 6371000.0
            delta_lat = np.degrees(north_dist / earth_radius)
            lat_rad = np.radians(prev_lat)
            delta_lon = np.degrees(east_dist / (earth_radius * np.cos(lat_rad)))
            expected_lat = prev_lat + delta_lat
            expected_lon = prev_lon + delta_lon

            # converting back to metres

            lat_error_rad = np.radians(self.reported_lat[plane] - expected_lat)
            lon_error_rad = np.radians(self.reported_lon[plane] - expected_lon)
            north_error = lat_error_rad * earth_radius

            east_error = (lon_error_rad* earth_radius * np.cos(np.radians(expected_lat)))   

            position_error = np.sqrt(north_error**2 + east_error**2)

            self.suspicion[plane] = position_error

            self.prev_reported_lat[plane] = self.reported_lat[plane]
            self.prev_reported_lon[plane] = self.reported_lon[plane]








