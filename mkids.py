from matplotlib import pyplot as plt
import numpy as np



class polygon(object):
    def __init__(self, polygon_id=100):
        self.__x_coords = []
        self.__y_coords = []
        self.__polygon_id = polygon_id
    def add_point(self, x, y):
        self.__x_coords.append(x)
        self.__y_coords.append(y)
    def clear_points(self):
        self.__x_coords = []
        self.__y_coords = []
    def get_points(self):
        return self.__x_coords, self.__y_coords
    def get_num_points(self):
        return len(self.__x_coords)
    def gen_sonnet_polygon(self):
        # Generate the polygon in the Sonnet format
        out_text = "0 5 0 N {} 1 1 100 100 0 0 0 Y".format(self.__polygon_id)
        # iterate through the points and add them to the output text
        for x, y in zip(self.__x_coords, self.__y_coords):
            # Add each point to the output text on a new line
            out_text += "\n{} {}".format(x, y)
        # Close the polygon by returning to the first point
        out_text += "\n{} {}".format(self.__x_coords[0], self.__y_coords[0]) 
        # finalise the polygon with the text "END"
        out_text += "\nEND"
        return out_text


class Rectangle(polygon):
    def __init__(self, x_0, y_0, dx, dy, polygon_id):
        super().__init__(polygon_id=polygon_id)
        self.set_start_height_breadth(x_0, y_0, dx, dy)
    def set_start_height_breadth(self, x_0, y_0, dx, dy):
        if self.get_num_points() > 0:
            raise ValueError("Rectangle points have already been set. Clear the points before setting new ones.")
        else:
            # Add the points to the polygon
            self.add_point(x_0,         y_0)
            self.add_point(x_0 + dx,    y_0)
            self.add_point(x_0 + dx,    y_0 + dy)
            self.add_point(x_0,         y_0 + dy)



class Port(object):
    """
    A Sonnet port attached to one edge of a polygon. Replaces the gen_port()
    function. The global ``polygon_name`` that gen_port read is now an explicit
    ``polygon_id`` -- the id of the polygon the port sits on -- passed in at
    construction. Call ``gen_sonnet_port()`` to render the .son definition.
    """

    def __init__(self, x, y, port_num, reference_plane, polygon_id,
                 port_type="BOX", resistance=50, reactance=0, inductance=0, capacitance=0):
        self.x = x                          # port x-coordinate (micrometres)
        self.y = y                          # port y-coordinate (micrometres)
        self.port_num = port_num            # Sonnet port number
        self.reference_plane = reference_plane
        self.polygon_id = polygon_id        # id of the polygon this port attaches to
        self.port_type = port_type
        self.resistance = resistance
        self.reactance = reactance
        self.inductance = inductance
        self.capacitance = capacitance

    def gen_sonnet_port(self):
        """Return the .son port-definition string."""
        return ("POR1 {}\n".format(self.port_type) +
                "POLY {} 1\n".format(self.polygon_id) +
                "{}\n".format(self.reference_plane) +
                "{} {} {} {} {} {} {}".format(self.port_num, self.resistance, self.reactance,
                                              self.inductance, self.capacitance, self.x, self.y))


class Geometry(object):
    def __init__(self, start_polygon_id=100):
        self.__polygons = []
        self.__current_polygon_id = start_polygon_id
    
    def get_polygons(self):
        return self.__polygons
    def get_num_polygons(self):
        return len(self.__polygons)
    def get_current_polygon(self):
        return self.__current_polygon_id
    def set_current_polygon(self, polygon_id):
        self.__current_polygon_id = polygon_id
    def get_polygons_string(self):
        out_string = ""
        for polygon in self.get_polygons():
            out_string += "\n{}".format(polygon.gen_sonnet_polygon())
        return out_string
    def add_polygon(self, polygon):
        self.__polygons.append(polygon)
    def _rect(self, origin_x, origin_y, direction, dx, dy, width, length):
        """
        Generate a single inductor rectangle, offset from (origin_x, origin_y).
        :param dx, dy: offset of the rectangle's origin from the passed origin
        :param width: x-extent (applied in the current direction)
        :param length: y-extent (drawn downward)
        :return: string containing the .son code for the rectangle
        """
        x0 = origin_x + (direction * dx)
        y0 = origin_y + dy
        
        self.add_polygon(Rectangle(x0, y0, (direction * width), length, polygon_id=self.__current_polygon_id))
        self.__current_polygon_id = self.__current_polygon_id + 1

class Capacitor(Geometry):
    """
    Generates Sonnet (.son) polygon code for an interdigitated capacitor:
    the rectangular frame plus alternating fingers and a final partial finger.

    Like Inductor, this subclasses Geometry and builds its shapes by appending
    ``rectangle`` objects to the inherited polygon list (via ``add_polygon``);
    call ``get_polygons_string()`` to render them. The standalone
    ``gen_sonnet_rectangle`` helper and its global ``polygon_name`` counter are
    no longer needed -- polygon ids are handled by the polygon/rectangle classes.

        cap = Capacitor(pitch=2.0, thick=1.0, length=10.0, num_fingers=4, ...)
        cap.generate()
        son_code = cap.get_polygons_string()

    Former globals map to attributes as follows:
        args.pitch       -> self.pitch
        args.thick       -> self.thick
        args.length      -> self.length
        args.num_fingers -> self.num_fingers
        args.final       -> self.final
        cap_left_out     -> self.cap_left_out
        cap_left_in      -> self.cap_left_in
        cap_right_in     -> self.cap_right_in
        cap_right_out    -> self.cap_right_out
        cap_top_out      -> self.cap_top_out
        cap_top_in       -> self.cap_top_in
        transfer_bar_in  -> self.transfer_bar_in
        transfer_bar_out -> self.transfer_bar_out
        transfer_bar_end -> self.transfer_bar_end
        ij_start         -> self.ij_start
        ij_end           -> self.ij_end

    Requires numpy (imported at module level as np), as in the original code.
    """

    def __init__(self,
                 finger_p=0.0, finger_b=0.0, finger_l=0.0, num_fingers=0, finger_lf=0.0,
                 x0=0.0, y0=0.0, xf=0.0, yf=0.0,
                 side_b=0.0, top_b=0.0, transfer_b=0, transfer_0=0.0,
                 ij_start=0.0, ij_end=0.0, start_polygon_id=100):
        super().__init__(start_polygon_id)
        # finger properties (formerly read from args)
        self.finger_p = finger_p              # centre-to-centre finger spacing
        self.finger_b = finger_b          # finger thickness
        self.finger_l = finger_l            # full finger length
        self.num_fingers = num_fingers  # number of full fingers
        self.finger_lf = finger_lf              # length of the trailing partial finger
        # capacitor frame boundaries
        self.x0 = x0
        self.y0 = y0
        self.xf = xf
        self.yf = yf
        # sidebar, top bar and transfer bar breadths
        self.side_b = side_b
        self.top_b = top_b
        self.transfer_b = transfer_b
        self.transfer_x0 = transfer_0
        # inductor-junction x extents (shared boundary with the inductor)
        self.ij_start = ij_start
        self.ij_end = ij_end

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def generate(self):
        """Build all capacitor polygons (frame + fingers) into the polygon list."""
        self._frame()
        self._fingers()

    def gen_ij_origin(self):
        origin_x = self.ij_start
        origin_y = self._y0_in()
        return origin_x, origin_y

        

    # ------------------------------------------------------------------ #
    # Internal calculated properties
    # ------------------------------------------------------------------ #
    def _x0_in(self):
        return self.x0 + self.side_b
    def _xf_in(self):
        return self.xf - self.side_b
    def _y0_in(self):
        return self.y0 + self.top_b
    def _yf_in(self):
        return self.yf - self.transfer_b
    def _finger_s(self):
        return self.finger_p - self.finger_b
    def _right_side_bar_l(self):
        return self.yf - self.y0
    def _left_side_bar_l(self):
        return self._right_side_bar_l() - (self._finger_s() + self.transfer_b)
    def _top_left_w(self):
        return self.ij_start - self._x0_in()
    def _top_right_w(self):
        return self._xf_in() - self.ij_end 
    def _transfer_w(self):
        return self._xf_in() - self.transfer_x0
    def _transfer_y0(self):
        return self.y0 + self._right_side_bar_l() - self.transfer_b
    def _in_w(self):
        return self._xf_in() - self._x0_in()


    # ------------------------------------------------------------------ #
    # Internal geometry helpers
    # ------------------------------------------------------------------ #
    def _frame(self):
        """Generate the five rectangles forming the capacitor outline and transfer bar."""
        origin_x, origin_y = 0, 0 #self.x0, self.y0
        direction = 1

        rects = [
            # dx,               dy,                    width,                  length
            (self.x0,           self.y0,               self.side_b,            self._left_side_bar_l() ),  # left side bar
            (self._x0_in(),     self.y0,               self._top_left_w(),     self.top_b              ),  # left top bar
            (self.ij_end,       self.y0,               self._top_right_w(),    self.top_b              ),  # right top bar
            (self._xf_in(),     self.y0,               self.side_b,            self._right_side_bar_l()),  # right side bar
            (self.transfer_x0,  self._transfer_y0(),   self._transfer_w(),     self.transfer_b         ),  # transfer bar
        ]

        for r in rects:
            self._rect(origin_x, origin_y, direction, *r) 
      
    def _fingers(self):
        """Generate the alternating full fingers plus the trailing partial finger."""
        origin_x = self._x0_in()
        origin_y = self.y0 + self._left_side_bar_l()

        direction = 1

        # need to leave room for the final (partial) finger
        #if (end_fingers - self.finger_p) < self._y0_in():
         #   raise OverflowError("Not enough room for the requested number of fingers.")

        rects = []

        # even index -> left side, odd index -> right side
        for i in range(self.num_fingers):
            rects.append(self._finger(i, self.finger_l))

        rects.append(self._finger(self.num_fingers, self.finger_lf))

        for r in rects:
            self._rect(origin_x, origin_y, direction, *r) 

    def _finger(self, number, length):
        dy = -(number * self.finger_p)
        right = bool(number % 2)
        if right:
            dx = self._in_w() - length
        else:
            dx = 0
        return (dx, dy, length, -self.finger_b)




class Inductor(Geometry):
    """
    Generates Sonnet (.son) polygon code for a spiral inductor with a junction.

    All geometry parameters are member variables and can be set from the
    outside: either pass them to the constructor, or assign the attributes
    after instantiation, e.g.

        ind = Inductor(turns=4, breadth=2.0, space=2.0, length=40.0, pitch=4.0)
        ind.ij_start = 0.0
        son_code = ind.generate()
    """

    def __init__(self,
                 turns=0,
                 breadth=0.0,
                 space=0.0,
                 length=0.0,
                 x0=0.0,
                 y0=0.0,
                 ij_b=0.0, 
                 start_polygon_id=100):
        super().__init__(start_polygon_id)
        # number of turns in the spiral
        self.turns = turns
        # conductor line breadth (thickness of each rectangle)
        self.breadth = breadth
        # spacing between adjacent conductor lines
        self.space = space
        # horizontal extent of a turn
        self.length = length
        # inductor-capacitor junction x/y origins
        self.x0 = x0
        self.y0 = y0
        # inductor-capacitor junction breadth
        self.ij_b = ij_b

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def generate(self):
        """
        Generate the polygons for the inductor.
        :return: string containing the .son code for the inductor
        """
        direction = 1
        origin_x, origin_y = self.x0, self.y0
        origin_x, origin_y = self._junction(origin_x, origin_y, direction)

        for i in range(self.turns):
            direction = (-1) ** i
            origin_x, origin_y = self._turn(origin_x, origin_y, direction)

        direction = (-1) ** self.turns
        self._end(origin_x, origin_y, direction)

        

    # ------------------------------------------------------------------ #
    # Internal calculated properties
    # ------------------------------------------------------------------ #
    def _out_l(self):
        # length of the outer endcap of a turn
        return (3 * self.space) + (4 * self.breadth)
    def _mid_l(self):
        # length of the inner endcap of a turn
        return (1 * self.space) + (2 * self.breadth)
    def _pitch(self):
        # vertical pitch between segments within a turn
        return self.breadth + self.space
    def _bar_l(self):
        # length of the bars of a turn
        return self.length - (2 * self._pitch())
    def _bar1_x0(self):
        return (2 * self.breadth) + self.space
    def _bar1_y0(self):
        return -(2 * self._pitch())
    def _bar2_x0(self):
        return self.breadth
    def _bar2_y0(self):
        return -(3 * self._pitch())
    def _ij_l1(self):
        return self.ij_b -  ((self.breadth * 2) + self.space)
    def _ij_l2(self):
        return self.ij_b -  self.breadth
    def inductor_height(self):
        return self.turns * self._pitch() * 2

    # ------------------------------------------------------------------ #
    # Internal geometry helpers
    # ------------------------------------------------------------------ #
    def _junction(self, origin_x, origin_y, direction):
        """
        Generate the polygons for the inductor junction.
        :return: (ij_string, origin_x, origin_y) for the first turn
        """


        rects = [
            # dx,              dy, width,         length
            (0,                0,  self.breadth,  -self._ij_l1()),
            (self._pitch(),    0,  self.breadth,  -self._ij_l2()),
        ]
        for r in rects:
            self._rect(origin_x, origin_y, direction, *r) 

        return origin_x, origin_y-self._ij_l1()

    def _turn(self, origin_x, origin_y, direction):
        """
        Generate one full turn (four rectangles) and the next origin.
        :return: (turn_string, final_x, final_y)
        """
        rects = [
            # dx,               dy,               width,          length
            (0,                 0,                self.breadth,   -self._out_l()   ),
            (self._pitch(),     -self._pitch(),   self.breadth,   -self._mid_l()   ),
            (self._bar1_x0(),   self._bar1_y0(),  self._bar_l(),  -self.breadth    ),
            (self._bar2_x0(),   self._bar2_y0(),  self._bar_l(),  -self.breadth    ),
        ]

        for r in rects:
            self._rect(origin_x, origin_y, direction, *r) 
        

        final_x = origin_x + (direction * self.length)
        final_y = origin_y - (2 * self._pitch())
        return final_x, final_y

    def _end(self, origin_x, origin_y, direction):
        """
        Generate the closing end segment (two rectangles).
        """
        rects = [
            # dx,            dy,           width,         length
            (0,              0,            self.breadth,  -self._mid_l()),
            (self.breadth,   -self._pitch(),   self._pitch(),    -self.breadth),
        ]
        for r in rects:
            self._rect(origin_x, origin_y, direction, *r) 


class GroundPlane(Geometry):
    """
    Generates Sonnet (.son) polygon code for the ground plane: a top bar, two
    resonator sidebars, three full-width horizontal bars carrying edge ports
    (the near bar, the feed line, and the opposite bar), and a final bar.

    Like the other Geometry subclasses, shapes are built by calling the
    inherited ``_rect`` primitive; rendered via ``get_polygons_string()``.
    Ports are a ground-plane-specific concept, so they are kept in a local list
    and rendered via ``get_ports_string()`` -- mirroring the two strings the
    original gen_ground_plane() returned (ports, polygons).

        gp = GroundPlane(x_size=..., y_size=..., resonator_top=..., ...)
        gp.generate()
        polygons = gp.get_polygons_string()
        ports = gp.get_ports_string()

    Former globals map to attributes as follows:
        args.x_size        -> self.x_size
        args.y_size        -> self.y_size
        resonator_top      -> self.resonator_top
        resonator_bottom   -> self.resonator_bottom
        gp_sidebar_breadth -> self.sidebar_b
        feed_line_breadth  -> self.feed_line_b
        gp_opp_breadth     -> self.opp_b
        feed_line_space    -> self.feed_line_space
        gp_split           -> self.gp_split
    """

    def __init__(self,
                 x0=0.0, y0=0.0,
                 x_size=0.0, y_size=0.0,
                 top_b=0.0, side_b=0.0, near_b=0.0, feed_b=0.0, oppo_b=0.0,
                 res_yl=0.0,          
                 feed_s=0.0, 
                 start_polygon_id=100):
        super().__init__(start_polygon_id)
        self.__ports = []
        self.x0 = x0
        self.y0 = y0
        # overall circuit size
        self.x_size = x_size
        self.y_size = y_size
        # resonator extents (shared boundary with the resonator)
        self.res_yl = res_yl
        # bar breadths
        self.top_b = top_b    # top bar before the resonator
        self.side_b = side_b  # resonator sidebars
        self.near_b = near_b  # near bar between resonator and feed line
        self.feed_b = feed_b  # feed line
        self.oppo_b = oppo_b  # bar opposite the feed line
        # vertical gap around the feed line
        self.feed_s = feed_s

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def generate(self):
        """Build all ground-plane polygons and ports."""
        origin_x, origin_y, direction = self.x0, self.y0, 1
        # top bar: full width, from the top of the circuit down to the resonator
        # left and right sidebars, running down either side of the resonator
        # final bar: full width, from the split line to the bottom of the circuit
        rects = [
            # dx,               dy,                 width,            length
            (0,                 0,                  self.x_size,        self.top_b),       # top bar
            (0,                 self.top_b,         self.side_b,     self.res_yl),      # left side bar
            (self._res_xf(),    self.top_b,         self.side_b,     self.res_yl),      # right side bar
            (0,                 self._final_y0(),   self.x_size,        self._final_b()),  # final bar
        ]

        for r in rects:
            self._rect(origin_x, origin_y, direction, *r) 
        """
        # top bar: full width, from the top of the circuit down to the resonator
        self._rect(origin_x, origin_y, direction, 0, 0, self.x_size, self.top_b)
        # left and right sidebars, running down either side of the resonator
        self._rect(origin_x, origin_y, direction,
                   0, self.top_b, self.resonator_left, self._sidebar_length())
        self._rect(origin_x, origin_y, direction,
                   self.x_size - self.sidebar_b, self.top_b, self.sidebar_b, self._sidebar_length())
        """
        port_num_ground = -1
        port_num_feed_l = 2
        port_num_feed_r = 1
        # near bar with ports, just below the resonator
        self._port_bar(self._near_y0(), self.near_b, port_num_ground, port_num_ground)
        # feed line with ports
        self._port_bar(self._feed_y0(), self.feed_b, port_num_feed_l, port_num_feed_r)
        # opposite ground-plane bar with ports
        self._port_bar(self._oppo_y0(), self.oppo_b, port_num_ground, port_num_ground)

        # final bar: full width, from the split line to the bottom of the circuit
        #self._rect(origin_x, origin_y, direction, 0, self.gp_split, self.x_size, self.y_size - self.gp_split)

    def add_port(self, port):
        self.__ports.append(port)

    def get_ports(self):
        return self.__ports

    def get_port_coords(self):
        """
        Extract the coordinates of every port on the ground plane.
        :return: (x_coords, y_coords) -- two parallel lists, matching the
                 convention of polygon.get_points() and ready to pass to
                 plt.scatter for plotting.
        """
        x_coords = [port.x for port in self.__ports]
        y_coords = [port.y for port in self.__ports]
        return x_coords, y_coords

    def get_ports_string(self):
        out_string = ""
        for port in self.__ports:
            out_string += "\n{}".format(port.gen_sonnet_port())
        return out_string

    def get_res_origin(self):
        return self._res_x0(), self._res_y0()
    def get_res_ending(self):
        return self._res_xf(), self._res_yf()

    # ------------------------------------------------------------------ #
    # Internal calculated properties
    # ------------------------------------------------------------------ #
    def _xf(self):
        return self.x0 + self.x_size
    def _yf(self):
        return self.y0 + self.y_size
    def _res_x0(self):
        return self.x0 + self.side_b
    def _res_xf(self):
        return self._xf() - self.side_b
    def _res_y0(self):
        return self.y0 + self.top_b
    def _res_yf(self):
        return self._res_y0() + self.res_yl
    def _near_y0(self):
        return self._res_yf()
    def _near_yf(self):
        return self._near_y0() + self.near_b
    def _feed_y0(self):
        return self._near_yf() + self.feed_s
    def _feed_yf(self):
        return self._feed_y0() + self.feed_b
    def _oppo_y0(self):
        return self._feed_yf() + self.feed_s
    def _opp_yf(self):
        return self._oppo_y0() + self.oppo_b
    def _final_y0(self):
        return self._opp_yf()
    def _final_b(self):
        return self._yf() - self._opp_yf()


    # ------------------------------------------------------------------ #
    # Internal geometry helpers
    # ------------------------------------------------------------------ #
    def _port_bar(self, top, breadth, port_num_l, port_num_r, reference_plane_l=1, reference_plane_r=3):
        """
        Draw a full-width horizontal bar and attach a port to each end.
        :param top: y-coordinate of the bar's top edge
        :param breadth: vertical thickness of the bar
        :param port_num_l / port_num_r: port numbers for the left/right edges
        :return: y-coordinate of the bar's bottom edge
        """
        origin_x, origin_y, direction = self.x0, self.y0, 1
        dx = 0

        # the bar takes the next polygon id; capture it so the ports can reference it
        bar_id = self.get_current_polygon()
        self._rect(origin_x, origin_y, direction, dx, top, self.x_size, breadth)

        # NOTE: kept from the original, but this puts the ports at top + 1.5*breadth
        # (below the bar), not the bar's vertical midpoint. If the midpoint was
        # intended, this should be top + (breadth / 2).
        midpoint = top + (breadth / 2)
        left = origin_x
        right = self._xf()
        # the original emits the right port before the left port
        self.add_port(Port(left,  midpoint, port_num_l, reference_plane_l, bar_id))
        self.add_port(Port(right, midpoint, port_num_r, reference_plane_r, bar_id))  
        

class Circuit(object):
    """
    Composes a GroundPlane, an Inductor, and a Capacitor into a single MKID
    circuit, resolving the handful of coordinates that are shared between them
    while leaving every other parameter independent (set by the caller when
    each geometry is constructed).

    Coupling handled here:
      * inductor_height = inductor.inductor_height() (turns x 2 x pitch).
      * The capacitor is placed inside the ground plane's resonator region:
            x0 = get_res_origin().x + cap_dx
            y0 = get_res_origin().y + (cap_dy + inductor_height)
            xf = get_res_ending().x - cap_dx
            yf = get_res_ending().y - cap_dy
        i.e. offset inward by cap_dx / cap_dy, leaving room above for the inductor.
      * The inductor is placed at the capacitor's junction origin,
        capacitor.gen_ij_origin().
      * Polygon ids run sequentially across all three geometries.

    Usage:
        gp  = GroundPlane(...)
        cap = Capacitor(...)   # its x0/y0/xf/yf are overwritten by the Circuit
        ind = Inductor(...)    # its x0/y0 are overwritten by the Circuit
        circuit = Circuit(gp, cap, ind, cap_dx=5.0, cap_dy=4.0, start_polygon_id=100)
        circuit.generate()
        son_code = circuit.get_sonnet_string()

    Requires these small additions to the existing classes:
        Geometry.set_current_polygon(self, polygon_id)
        GroundPlane.get_res_origin(self)   -> (resonator_left, resonator_top)
        GroundPlane.get_res_ending(self)   -> (x_size - sidebar_b, resonator_bottom)
        Inductor.inductor_height(self)     -> turns * pitch
    """

    def __init__(self, ground_plane, capacitor, inductor,
                 cap_dx=0.0, cap_dy=0.0, start_polygon_id=100):
        self.__ground_plane = ground_plane
        self.__capacitor = capacitor
        self.__inductor = inductor
        # inward offsets of the capacitor frame from the resonator region
        self.cap_dx = cap_dx
        self.cap_dy = cap_dy
        # polygon id the first polygon of the whole circuit will take
        self.start_polygon_id = start_polygon_id
        self.__generated = False
        # resolve the shared coordinates up front so the sub-geometries are
        # fully positioned before anything is generated
        self.__place()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def generate(self):
        """
        Generate every polygon and port. Geometries are generated in order and
        their polygon-id counters chained, so ids are unique and sequential
        across the ground plane, inductor, and capacitor. Idempotent.
        """
        if self.__generated:
            return

        self.__ground_plane.set_current_polygon(self.start_polygon_id)
        self.__ground_plane.generate()

        self.__inductor.set_current_polygon(self.__ground_plane.get_current_polygon())
        self.__inductor.generate()

        self.__capacitor.set_current_polygon(self.__inductor.get_current_polygon())
        self.__capacitor.generate()

        self.__generated = True

    def get_sonnet_string(self):
        """
        Return the combined Sonnet code: all ports, then the polygon count,
        then all polygons -- across the three geometries, in id order.
        """
        ports_string = self.__ground_plane.get_ports_string()
        polygons_string = (self.__ground_plane.get_polygons_string() +
                           self.__inductor.get_polygons_string() +
                           self.__capacitor.get_polygons_string())
        num_polygons = (self.__ground_plane.get_num_polygons() +
                        self.__inductor.get_num_polygons() +
                        self.__capacitor.get_num_polygons())
        return ports_string + "\nNUM " + str(num_polygons) + polygons_string

    def get_polygons(self):
        polygons = []
        polygons.extend(self.__ground_plane.get_polygons())
        polygons.extend(self.__capacitor.get_polygons())
        polygons.extend(self.__inductor.get_polygons())
        return polygons

    def get_ground_plane(self):
        return self.__ground_plane

    def get_capacitor(self):
        return self.__capacitor

    def get_inductor(self):
        return self.__inductor

    # ------------------------------------------------------------------ #
    # Internal wiring
    # ------------------------------------------------------------------ #
    def __place(self):
        """Resolve the coordinates shared between the three geometries."""
        inductor_height = self.__inductor.inductor_height()

        res_origin_x, res_origin_y = self.__ground_plane.get_res_origin()
        res_end_x, res_end_y = self.__ground_plane.get_res_ending()

        # capacitor sits inside the resonator region, leaving room for the
        # inductor above it
        self.__capacitor.x0 = res_origin_x + self.cap_dx
        self.__capacitor.y0 = res_origin_y + (self.cap_dy + inductor_height)
        self.__capacitor.xf = res_end_x - self.cap_dx
        self.__capacitor.yf = res_end_y - self.cap_dy

        # inductor sits at the capacitor's inductor-junction origin (depends on
        # the capacitor's y0, which was just set)
        self.__inductor.x0, self.__inductor.y0 = self.__capacitor.gen_ij_origin()
        self.__inductor.ij_b = self.__capacitor.top_b



class Dielectric(object):
    """
    Represents a Sonnet dielectric layer and renders it to .son format.

    Properties:
        name                  -- layer name (string), emitted in double quotes
        thickness             -- layer thickness (float)
        erel                  -- relative permittivity (float)
        mrel                  -- relative permeability (float)
        dielectric_loss_tan   -- dielectric loss tangent (float)
        conductivity          -- dielectric conductivity (float)
        mag_loss_tan          -- magnetic loss tangent (float)
        anisotropic           -- bool. When True, a second set of every float
                                 property except thickness is required (the
                                 *_2 attributes), describing the second
                                 (normal) direction.

    All parameters can be set via the constructor or by assignment afterwards.
    The *_2 attributes default to None; they only need values when anisotropic
    is True, at which point gen_sonnet_dielectric() enforces that they are set.
    """

    def __init__(self, name="", thickness=0.0,
                 erel=0.0, mrel=0.0, dielectric_loss_tan=0.0,
                 conductivity=0.0, mag_loss_tan=0.0,
                 anisotropic=False,
                 erel_2=None, mrel_2=None, dielectric_loss_tan_2=None,
                 conductivity_2=None, mag_loss_tan_2=None):
        self.name = name
        self.thickness = thickness
        # first set of properties
        self.erel = erel
        self.mrel = mrel
        self.dielectric_loss_tan = dielectric_loss_tan
        self.conductivity = conductivity
        self.mag_loss_tan = mag_loss_tan
        self.anisotropic = anisotropic
        # second set, required only when anisotropic is True
        self.erel_2 = erel_2
        self.mrel_2 = mrel_2
        self.dielectric_loss_tan_2 = dielectric_loss_tan_2
        self.conductivity_2 = conductivity_2
        self.mag_loss_tan_2 = mag_loss_tan_2

    def gen_sonnet_dielectric(self):
        """
        Return the space-separated .son representation of the layer:

            thickness erel mrel dielectric_loss_tan conductivity mag_loss_tan "name"

        and, when anisotropic, an 'A' flag followed by the second set:

            ... "name" A erel_2 mrel_2 dielectric_loss_tan_2 conductivity_2 mag_loss_tan_2
        """
        first_set = [self.thickness, self.erel, self.mrel,
                     self.dielectric_loss_tan, self.conductivity, self.mag_loss_tan]
        out_text = " ".join(str(value) for value in first_set) + ' "{}"'.format(self.name)

        if self.anisotropic:
            second_set = [self.erel_2, self.mrel_2, self.dielectric_loss_tan_2,
                          self.conductivity_2, self.mag_loss_tan_2]
            if any(value is None for value in second_set):
                raise ValueError("Anisotropic dielectric requires the second set "
                                 "of properties (the *_2 attributes) to be set.")
            out_text += " A " + " ".join(str(value) for value in second_set)

        return out_text


ground_plane = GroundPlane(x_size=500.0, y_size=500.0,
                           top_b=500.0-348.0, res_yl=348-173,
                           side_b=12.0, near_b=12.0, feed_b=35.0, oppo_b=25.0,
                           feed_s=5.0, 
                           start_polygon_id=100)

capacitor = Capacitor(finger_p=4.0, finger_b=2.0, finger_l=450.0, num_fingers=27, finger_lf=84.0,
                      side_b=7.0, top_b=10.0, transfer_b=5.0, transfer_0=250.0,
                      ij_start=240.0, ij_end=243.0)


inductor = Inductor(turns=5,
            breadth=1.0,
            space=1.0,
            length=20.0)

circuit = Circuit(ground_plane=ground_plane, capacitor=capacitor, inductor=inductor,
                  cap_dx=4.0, cap_dy=4.0)

circuit.generate()


#polygons=inductor.get_polygons()
print(circuit.get_sonnet_string())
plt.figure()

polygons=circuit.get_polygons()
num = len(polygons)
# creates a set of colours using the red colourmap
colors = plt.cm.Reds(np.linspace(0.2, 1, num))
for i in range(num):
    x,y = polygons[i].get_points()
    plt.fill(x,y,color=colors[i])

"""
polygons=capacitor.get_polygons()
num = len(polygons)
# creates a set of colours using the Blue colourmap
colors = plt.cm.Blues(np.linspace(0.2, 1, num))
for i in range(num):
    x,y = polygons[i].get_points()
    plt.fill(x,y,color=colors[i])


polygons=inductor.get_polygons()
num = len(polygons)
# creates a set of colours using the Greens colourmap
colors = plt.cm.Greens(np.linspace(0.2, 1, num))
for i in range(num):
    x,y = polygons[i].get_points()
    plt.fill(x,y,color=colors[i])
"""

x,y = ground_plane.get_port_coords()
plt.plot(x,y,'s',color="goldenrod")

plt.show()

plt.close()
