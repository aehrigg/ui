const base = import.meta.env.VITE_API_BASE ?? '';

async function handleResponse(res) {
	if (!res.ok) {
		const text = await res.text();
		throw new Error(text || `Request failed with status ${res.status}`);
	}
	return res.json();
}

export async function getStatus() {
	const res = await fetch(`${base}/api/status`);
	return handleResponse(res);
}

export async function setMode(mode) {
	const res = await fetch(`${base}/api/mode`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ mode })
	});
	return handleResponse(res);
}

export async function setTarget(satellite_id) {
	const res = await fetch(`${base}/api/target`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ satellite_id })
	});
	return handleResponse(res);
}

export async function sendManual(command) {
	const res = await fetch(`${base}/api/manual`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ command })
	});
	return handleResponse(res);
}
