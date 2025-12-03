<script>
	import { onMount } from 'svelte';
	import { getStatus, setMode, setTarget, sendManual } from '$lib/api.js';

	const satelliteOptions = [
		{ id: 25544, name: 'ISS (ZARYA)' },
		{ id: 40069, name: 'METEOR M2' },
		{ id: 33591, name: 'NOAA 19' }
	];

	let status = {
		position: { azimuth: 0, elevation: 0 },
		mode: 'geo',
		satellite_id: satelliteOptions[0].id,
		signal: null
	};

	let selectedSatellite = satelliteOptions[0].id;
	let loading = false;
	let error = '';
	let connectionState = 'idle';
	let pollingHandle;

	async function fetchStatus() {
		try {
			connectionState = 'loading';
			const data = await getStatus();
			status = data;
			selectedSatellite = data.satellite_id;
			connectionState = 'ok';
			error = '';
		} catch (err) {
			connectionState = 'error';
			error = err?.message ?? 'Konnte Status nicht laden';
		}
	}

	async function changeMode(mode) {
		try {
			loading = true;
			await setMode(mode);
			status = { ...status, mode };
		} catch (err) {
			error = err?.message ?? 'Modus konnte nicht geändert werden';
		} finally {
			loading = false;
		}
	}

	async function changeSatellite(id) {
		try {
			loading = true;
			await setTarget(Number(id));
			status = { ...status, satellite_id: Number(id) };
		} catch (err) {
			error = err?.message ?? 'Satellit konnte nicht gesetzt werden';
		} finally {
			loading = false;
		}
	}

	async function sendManualCommand(direction) {
		try {
			loading = true;
			await sendManual(direction);
		} catch (err) {
			error = err?.message ?? 'Befehl konnte nicht gesendet werden';
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		fetchStatus();
		pollingHandle = setInterval(fetchStatus, 5000);
		return () => clearInterval(pollingHandle);
	});
</script>

<main class="p-6 max-w-3xl mx-auto font-sans space-y-8">
	<header class="flex items-center justify-between">
		<h1 class="text-2xl font-bold">Satellitensteuerung</h1>
		<span
			class="text-xs px-2 py-1 rounded font-semibold"
			class:bg-green-200={connectionState === 'ok'}
			class:bg-yellow-200={connectionState === 'loading'}
			class:bg-red-200={connectionState === 'error'}
		>
			{connectionState === 'ok'
				? 'Verbunden'
				: connectionState === 'loading'
					? 'Lädt …'
					: 'Keine Verbindung'}
		</span>
	</header>

	{#if error}
		<div class="bg-red-100 text-red-800 p-3 rounded">{error}</div>
	{/if}

	<section class="bg-gray-100 p-4 rounded-xl shadow space-y-2">
		<h2 class="text-xl font-semibold mb-2">Status</h2>
		<p>
			Azimut:
			<strong>{status.position.azimuth?.toFixed(1) ?? '–'}°</strong>
		</p>
		<p>
			Elevation:
			<strong>{status.position.elevation?.toFixed(1) ?? '–'}°</strong>
		</p>
		<p>
			Signalstärke:
			<strong>{status.signal ?? '–'}%</strong>
		</p>
		<div class="w-full bg-gray-300 h-4 rounded">
			<div
				class="bg-green-500 h-4 rounded transition-all duration-300"
				style={`width: ${status.signal ?? 0}%`}
			></div>
		</div>
	</section>

	<section class="bg-gray-100 p-4 rounded-xl shadow space-y-2">
		<h2 class="text-xl font-semibold mb-2">Betriebsmodus</h2>
		<select
			bind:value={status.mode}
			on:change={(e) => changeMode(e.target.value)}
			class="w-full p-2 border rounded"
			disabled={loading}
		>
			<option value="geo">Automatik – geostationär</option>
			<option value="polar">Automatik – polumlaufend</option>
			<option value="manual">Manuell</option>
		</select>
	</section>

	<section class="bg-gray-100 p-4 rounded-xl shadow space-y-2">
		<h2 class="text-xl font-semibold mb-2">Satellitenauswahl</h2>
		<select
			bind:value={selectedSatellite}
			on:change={(e) => changeSatellite(e.target.value)}
			class="w-full p-2 border rounded"
			disabled={loading}
		>
			{#each satelliteOptions as sat}
				<option value={sat.id}>{sat.name} (ID {sat.id})</option>
			{/each}
		</select>
		<p class="mt-2 text-sm text-gray-600">
			Aktuell ausgewählt: <strong>{selectedSatellite}</strong>
		</p>
	</section>

	<section class="bg-gray-100 p-4 rounded-xl shadow space-y-3">
		<h2 class="text-xl font-semibold mb-2">Manuelle Steuerung</h2>
		<div class="grid grid-cols-3 gap-2 w-40 mx-auto">
			<button class="bg-blue-500 text-white rounded p-2" on:click={() => sendManualCommand('up')}>
				↑
			</button>
			<div></div>
			<button class="bg-blue-500 text-white rounded p-2" on:click={() => sendManualCommand('right')}>
				→
			</button>
			<button class="bg-blue-500 text-white rounded p-2" on:click={() => sendManualCommand('left')}>
				←
			</button>
			<div></div>
			<button class="bg-blue-500 text-white rounded p-2" on:click={() => sendManualCommand('down')}>
				↓
			</button>
		</div>
	</section>
</main>
