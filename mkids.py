from token import STAR

from matplotlib import pyplot as plt
import numpy as np

class mkid(object):
    def __init__(self):
        self.__resonator = resonator()

    pass


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
        return out_text


class rectangle(polygon):
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
        
        self.add_polygon(rectangle(x0, y0, (direction * width), length, polygon_id=self.__current_polygon_id))
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
        super().__init__()
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
        


class resonator(object):
    def __init__(self):
        self.__bottom = 0.0
        self.__top = 0.0
        self.__left = 0.0
        self.__right = 0.0
        self.__inductor = Inductor()
        self.__capacitor = Capacitor()




capacitor = Capacitor(finger_p=4.0, finger_b=2.0, finger_l=450.0, num_fingers=27, finger_lf=84.0,
                 x0=17.0, y0=500.0-343, xf=483.0, yf=500-175.0,
                 side_b=7.0, top_b=10.0, transfer_b=4, transfer_0=250.0,
                 ij_start=240.0, ij_end=243.0)
capacitor.generate()

ind_x0, ind_y0 = capacitor.gen_ij_origin()
start_ind_polygon_id = capacitor.get_current_polygon()

inductor = Inductor(turns=6,
            breadth=1.0,
            space=1.0,
            length=20.0,
            x0=ind_x0,
            y0=ind_y0,
            ij_b=10.0,
            start_polygon_id=start_ind_polygon_id)
inductor.generate()

polygons=capacitor.get_polygons()
#polygons=inductor.get_polygons()
print(inductor.get_polygons_string())
plt.figure()

num = len(polygons)

# creates a set of colours using the Blue colourmap
colors = plt.cm.Blues(np.linspace(0.2, 1, num))

for i in range(num):
    x,y = polygons[i].get_points()
    plt.fill(x,y,color=colors[i])


polygons=inductor.get_polygons()
num = len(polygons)
for i in range(num):
    x,y = polygons[i].get_points()
    plt.fill(x,y,color="green")


plt.show()

plt.close()
