use pyo3::prelude::*;

#[pyfunction]
fn space(_py: Python<'_>, points: Vec<(f32, f32)>, distance: usize) -> PyResult<Vec<(f32, f32)>> {
	println!("Spacing out points...");
	let mut points = points.clone();
	let distance = distance as f32;
	let mut min_distance_total = 0.0;
	for _ in 0..20000 {
		let mut directions = vec![(0.0, 0.0); points.len()];
		let mut min_distance = distance * 2.0;
		let mut points_next = points.clone();
		for (a, point_a) in points.iter().copied().enumerate() {
			for (b, point_b) in points.iter().skip(a + 1).copied().enumerate() {
				let mut vector = (point_b.0 - point_a.0, point_b.1 - point_a.1);
				let norm = norm(vector);
				min_distance = min_distance.min(norm);
				vector.0 /= norm;
				vector.1 /= norm;
				if norm <= distance {
					directions[b].0 += vector.0 / (norm * norm);
					directions[b].1 += vector.1 / (norm * norm);

					directions[a].0 -= vector.0 / (norm * norm);
					directions[a].1 -= vector.1 / (norm * norm);
				}
			}
		}
		for (index, (point, mut displacement)) in points.iter().zip(directions).enumerate() {
			if norm(displacement) > distance / 10.0 {
				displacement.0 *= (distance / 10.0) / norm(displacement);
				displacement.1 *= (distance / 10.0) / norm(displacement);
			}
			points_next[index].0 = point.0 + displacement.0;
			points_next[index].1 = point.1 + displacement.1;
		}
		points = points_next;
		min_distance_total = min_distance;
		if min_distance >= distance {
			println!("Minimum distance: {}", min_distance);
			return Ok(points);
		}
	}
	eprintln!("Minimum distance still too small: {}", min_distance_total);
	Ok(points)
}

fn norm(point: (f32, f32)) -> f32 {
	(point.0 * point.0 + point.1 * point.1).sqrt()
}

/// A Python module implemented in Rust.
#[pymodule]
fn fast_spacing(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(space, m)?)?;
    Ok(())
}