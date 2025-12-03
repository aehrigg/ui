<script>
  // Dummy-Statusdaten
  let azimuth = 142;
  let elevation = 36;
  let signal = 76;

  let mode = "geo";
  let satellites = ["Astra 19.2E", "NOAA-19", "Iridium 95"];
  let selectedSatellite = satellites[0];
</script>

<main class="p-6 max-w-3xl mx-auto font-sans space-y-8">
  <h1 class="text-2xl font-bold">Satellitensteuerung</h1>

  <!-- Statusanzeige -->
  <section class="bg-gray-100 p-4 rounded-xl shadow">
    <h2 class="text-xl font-semibold mb-2">Status</h2>
    <p>Azimut: <strong>{azimuth}°</strong></p>
    <p>Elevation: <strong>{elevation}°</strong></p>
    <p>Signalstärke: <strong>{signal}%</strong></p>
    <div class="w-full bg-gray-300 h-4 rounded">
      <div class="bg-green-500 h-4 rounded" style="width: {signal}%"></div>
    </div>
  </section>

  <!-- Betriebsmodus -->
  <section class="bg-gray-100 p-4 rounded-xl shadow">
    <h2 class="text-xl font-semibold mb-2">Betriebsmodus</h2>
    <select bind:value={mode} class="w-full p-2 border rounded">
      <option value="geo">Automatik – geostationär</option>
      <option value="polar">Automatik – polumlaufend</option>
      <option value="manual">Manuell</option>
    </select>
  </section>

  <!-- Satellitenliste -->
  <section class="bg-gray-100 p-4 rounded-xl shadow">
    <h2 class="text-xl font-semibold mb-2">Satellitenauswahl</h2>
    <select bind:value={selectedSatellite} class="w-full p-2 border rounded">
      {#each satellites as sat}
        <option>{sat}</option>
      {/each}
    </select>
    <p class="mt-2 text-sm text-gray-600">Aktuell ausgewählt: <strong>{selectedSatellite}</strong></p>
  </section>

  <!-- Steuerung (Dummy) -->
  <section class="bg-gray-100 p-4 rounded-xl shadow">
    <h2 class="text-xl font-semibold mb-2">Manuelle Steuerung</h2>
    <div class="grid grid-cols-3 gap-2 w-40 mx-auto">
      <button class="bg-blue-500 text-white rounded p-2">↑</button>
      <div></div>
      <button class="bg-blue-500 text-white rounded p-2">→</button>
      <button class="bg-blue-500 text-white rounded p-2">←</button>
      <div></div>
      <button class="bg-blue-500 text-white rounded p-2">↓</button>
    </div>
  </section>
</main>

<style>
  main {
    font-family: system-ui, sans-serif;
  }
</style>
