<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" encoding="UTF-8"/>
  <xsl:template match="/featureMap">
    <html>
      <head>
        <meta charset="UTF-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title><xsl:value-of select="meta/feature"/> - Feature Map</title>
        <style>
          body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;max-width:1180px;margin:2rem auto;padding:0 1rem;line-height:1.55;color:#202124;background:#fff}
          header{border-bottom:2px solid #ddd;margin-bottom:1.5rem} h1{margin-bottom:.25rem} h2{margin-top:1.8rem;border-bottom:1px solid #ddd;padding-bottom:.25rem}
          h3{margin:.15rem 0 .75rem;font-size:1rem}.meta,.tag{color:#555}.tag{display:inline-block;border:1px solid #ccc;border-radius:999px;padding:.1rem .5rem;margin-right:.35rem;font-size:.85rem}
          table{border-collapse:collapse;width:100%;margin:.5rem 0} th,td{border:1px solid #ddd;padding:.45rem;text-align:left;vertical-align:top} th{background:#f5f5f5}
          code,pre{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}.open-high{font-weight:700}
          .diagram-card{border:1px solid #ddd;border-radius:.6rem;padding:1rem;margin:1rem 0;overflow:auto}.diagram-meta{color:#666;font-size:.85rem;margin-bottom:.5rem}
          .mermaid{text-align:center;min-width:320px}.mermaid-error{color:#a00;white-space:pre-wrap;text-align:left}.mermaid-status{font-size:.85rem;color:#666}
        </style>
      </head>
      <body>
        <header>
          <h1><xsl:value-of select="meta/feature"/></h1>
          <p class="meta"><xsl:value-of select="meta/system"/> · <span class="tag"><xsl:value-of select="@mode"/></span><span class="tag"><xsl:value-of select="@state"/></span></p>
        </header>
        <h2>Goal</h2>
        <p><strong>Purpose:</strong> <xsl:value-of select="goal/purpose"/></p>
        <xsl:if test="goal/done"><p><strong>Done:</strong> <xsl:value-of select="goal/done"/></p></xsl:if>
        <xsl:if test="goal/scope"><p><strong>Scope:</strong> <xsl:value-of select="goal/scope"/></p></xsl:if>
        <xsl:if test="goal/exclude"><p><strong>Exclude:</strong> <xsl:value-of select="goal/exclude"/></p></xsl:if>

        <xsl:if test="useCase">
          <h2>Use Cases</h2>
          <xsl:for-each select="useCase"><p><strong><xsl:value-of select="@id"/>:</strong> <xsl:value-of select="scenario"/><xsl:if test="sample"><br/><span class="meta">Sample: <xsl:value-of select="sample"/></span></xsl:if></p></xsl:for-each>
        </xsl:if>

        <h2>Source Map</h2>
        <table><tr><th>Kind</th><th>Target</th><th>Access</th></tr>
          <xsl:for-each select="sourceMap/ref"><tr><td><xsl:value-of select="@kind"/></td><td><code><xsl:value-of select="@target"/></code></td><td><xsl:value-of select="@access"/></td></tr></xsl:for-each>
        </table>

        <xsl:if test="diagrams/diagram">
          <h2>Diagrams</h2>
          <p id="mermaid-status" class="mermaid-status">Mermaidを読み込み中です。描画できない場合も、図のソースはそのまま表示されます。</p>
          <xsl:for-each select="diagrams/diagram">
            <section class="diagram-card">
              <h3><xsl:choose><xsl:when test="@title"><xsl:value-of select="@title"/></xsl:when><xsl:otherwise><xsl:value-of select="@id"/></xsl:otherwise></xsl:choose></h3>
              <div class="diagram-meta"><xsl:value-of select="@kind"/><xsl:if test="@id"> · <xsl:value-of select="@id"/></xsl:if></div>
              <pre class="mermaid"><xsl:value-of select="."/></pre>
            </section>
          </xsl:for-each>
        </xsl:if>

        <xsl:if test="knowledge/*">
          <h2>Knowledge</h2>
          <ul><xsl:for-each select="knowledge/*"><li><strong><xsl:value-of select="local-name()"/><xsl:if test="@id"> <xsl:value-of select="@id"/></xsl:if>:</strong> <xsl:value-of select="."/><xsl:if test="@reason"> <span class="meta">(reason: <xsl:value-of select="@reason"/>)</span></xsl:if></li></xsl:for-each></ul>
        </xsl:if>

        <xsl:if test="verify/case">
          <h2>Verify</h2>
          <table><tr><th>ID</th><th>Type</th><th>Status</th><th>Condition</th><th>Expect / Observe</th></tr>
            <xsl:for-each select="verify/case"><tr><td><xsl:value-of select="@id"/></td><td><xsl:value-of select="@type"/></td><td><xsl:value-of select="@status"/></td><td><xsl:value-of select="condition"/></td><td><xsl:value-of select="expect"/><xsl:if test="observe"><br/><span class="meta">Observed: <xsl:value-of select="observe"/></span></xsl:if></td></tr></xsl:for-each>
          </table>
        </xsl:if>

        <xsl:if test="open/item">
          <h2>Open</h2>
          <ul><xsl:for-each select="open/item"><li><xsl:if test="@impact='high'"><xsl:attribute name="class">open-high</xsl:attribute></xsl:if><strong><xsl:value-of select="@id"/> [<xsl:value-of select="@impact"/><xsl:if test="@type"> / <xsl:value-of select="@type"/></xsl:if>]:</strong> <xsl:value-of select="."/> <span class="meta">→ <xsl:value-of select="@next"/></span></li></xsl:for-each></ul>
        </xsl:if>

        <xsl:if test="diagrams/diagram">
          <script><![CDATA[
(function () {
  const LOCAL = 'feature-map.mermaid.min.js';
  const CDN = 'https://cdn.jsdelivr.net/npm/mermaid@12.0.0/dist/mermaid.min.js';
  const status = document.getElementById('mermaid-status');

  function showError(message) {
    if (status) status.textContent = message;
    document.querySelectorAll('.mermaid').forEach(function (node) {
      node.classList.add('mermaid-error');
    });
  }

  async function render() {
    try {
      window.mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', layout: 'dagre', theme: 'default', look: 'classic' });
      await window.mermaid.run({ querySelector: '.mermaid' });
      if (status) status.textContent = 'Mermaid 12.0.0 で描画しました。';
    } catch (error) {
      showError('Mermaidの描画に失敗しました。図のソースを確認してください: ' + String(error));
    }
  }

  function load(src, fallback) {
    const script = document.createElement('script');
    script.src = src;
    script.onload = render;
    script.onerror = function () {
      if (fallback) load(fallback, null);
      else showError('Mermaidを読み込めませんでした。feature-map.mermaid.min.js を配置するか、ネットワーク接続を確認してください。');
    };
    document.head.appendChild(script);
  }

  if (window.mermaid) render();
  else load(LOCAL, CDN);
})();
          ]]></script>
        </xsl:if>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
