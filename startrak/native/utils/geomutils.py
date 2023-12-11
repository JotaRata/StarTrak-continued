# Compiled module

import math
from startrak.native.collections.position import Position, PositionArray

def distance(p1 : Position, p2 : Position) -> float:
	d = p1 - p2
	return d.x ** 2 + d.y ** 2

def angle(s1 : float, s2 : float, s3 : float) -> float:
	return math.degrees(math.acos((s1**2 + s2**2 - s3**2) / (2 * s1 * s2)))

def area(trig : PositionArray) -> float:
		a = distance(trig[0], trig[1])
		b = distance(trig[1], trig[2])
		c = distance(trig[2], trig[0])
		s = (a + b + c) / 2
		return math.sqrt(s * (s - a) * (s - b) * (s - c))

# Triangle congruence
def congruence_aaa(trig1: PositionArray, trig2: PositionArray, tolerance: float = 0.05) -> bool:
	a1, b1, c1 = distance(trig1[0], trig1[1]), distance(trig1[0], trig1[2]), distance(trig1[1], trig1[2])
	a2, b2, c2 = distance(trig2[0], trig2[1]), distance(trig2[0], trig2[2]), distance(trig2[1], trig2[2])

	angle1_0 = angle(a1, b1, c1)
	angle1_1 = angle(b1, c1, a1)
	angle1_2 = angle(c1, a1, b1)

	angle2_0 = angle(a2, b2, c2)
	angle2_1 = angle(b2, c2, a2)
	angle2_2 = angle(c2, a2, b2)

	diff_0 = abs(angle1_0 - angle2_0)
	diff_1 = abs(angle1_1 - angle2_1)
	diff_2 = abs(angle1_2 - angle2_2)
	return all(diff < tolerance for diff in [diff_0, diff_1, diff_2])

def congruence_sss(trig1: PositionArray, trig2: PositionArray, tolerance: float = 0.05) -> bool:
	a1, b1, c1 = distance(trig1[0], trig1[1]), distance(trig1[0], trig1[2]), distance(trig1[1], trig1[2])
	a2, b2, c2 = distance(trig2[0], trig2[1]), distance(trig2[0], trig2[2]), distance(trig2[1], trig2[2])

	diff_a = abs(a1 - a2)
	diff_b = abs(b1 - b2)
	diff_c = abs(c1 - c2)
	return all(diff < tolerance for diff in [diff_a, diff_b, diff_c])

def ongruence_sas(trig1: PositionArray, trig2: PositionArray, tolerance: float = 0.05) -> bool:
	a1, b1, c1 = distance(trig1[0], trig1[1]), distance(trig1[0], trig1[2]), distance(trig1[1], trig1[2])
	a2, b2, c2 = distance(trig2[0], trig2[1]), distance(trig2[0], trig2[2]), distance(trig2[1], trig2[2])

	angle1_0 = angle(a1, b1, c1)
	angle1_1 = angle(b1, c1, a1)
	angle1_2 = angle(c1, a1, b1)

	angle2_0 = angle(a2, b2, c2)
	angle2_1 = angle(b2, c2, a2)
	angle2_2 = angle(c2, a2, b2)

	diff_0 = abs(angle1_0 - angle2_0)
	diff_1 = abs(angle1_1 - angle2_1)
	diff_2 = abs(angle1_2 - angle2_2)

	diff_a = abs(a1 - a2)
	diff_b = abs(b1 - b2)
	diff_c = abs(c1 - c2)
	return all(diff < tolerance for diff in [diff_0, diff_1, diff_2, diff_a, diff_b, diff_c])