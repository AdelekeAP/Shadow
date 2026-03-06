import { useState, useMemo } from 'react'

/* ═══════════════════════════════════════════════════════════════
   ConceptDiagram — Interactive SVG concept diagram renderer
   Renders AI-generated node/edge graphs with 5 layout algorithms.
   Designed to match Shadow's navy/surface design system.
   ═══════════════════════════════════════════════════════════════ */

/* ─── Node palette — matches Shadow's semantic color tokens ─── */
const NODE_COLORS = {
  concept:  { fill: '#f0f4ff', stroke: '#c7d7fe', text: '#1e3a5f', badge: '#1e3a8a', badgeBg: 'bg-navy-800',     tagBg: 'bg-navy-50',     tagText: 'text-navy-700',     tagBorder: 'border-navy-200/60' },
  process:  { fill: '#ecfdf5', stroke: '#a7f3d0', text: '#065f46', badge: '#059669', badgeBg: 'bg-emerald-600',  tagBg: 'bg-emerald-50',  tagText: 'text-emerald-700',  tagBorder: 'border-emerald-200/60' },
  example:  { fill: '#fffbeb', stroke: '#fde68a', text: '#92400e', badge: '#d97706', badgeBg: 'bg-amber-500',    tagBg: 'bg-amber-50',    tagText: 'text-amber-700',    tagBorder: 'border-amber-200/60' },
  category: { fill: '#f5f3ff', stroke: '#c4b5fd', text: '#5b21b6', badge: '#7c3aed', badgeBg: 'bg-violet-600',   tagBg: 'bg-violet-50',   tagText: 'text-violet-700',   tagBorder: 'border-violet-200/60' },
  outcome:  { fill: '#fff7ed', stroke: '#fed7aa', text: '#9a3412', badge: '#ea580c', badgeBg: 'bg-orange-500',   tagBg: 'bg-orange-50',   tagText: 'text-orange-700',   tagBorder: 'border-orange-200/60' },
}

const NODE_WIDTH = 160
const NODE_HEIGHT = 58
const COMPACT_SCALE = 0.85

/* ─── Layout Algorithms ─── */

function layoutTree(nodes, edges) {
  const positions = new Map()
  const levels = new Map()
  nodes.forEach(n => {
    const lvl = n.level || 0
    if (!levels.has(lvl)) levels.set(lvl, [])
    levels.get(lvl).push(n.id)
  })
  const sortedLevels = [...levels.keys()].sort((a, b) => a - b)
  const maxNodesInLevel = Math.max(...[...levels.values()].map(l => l.length), 1)
  const canvasW = Math.max(800, maxNodesInLevel * (NODE_WIDTH + 40))
  sortedLevels.forEach(lvl => {
    const ids = levels.get(lvl)
    const spacing = canvasW / (ids.length + 1)
    ids.forEach((id, i) => { positions.set(id, { x: spacing * (i + 1), y: 60 + lvl * 120 }) })
  })
  const maxY = Math.max(...[...positions.values()].map(p => p.y), 0)
  return { positions, viewBox: `0 0 ${canvasW} ${maxY + 100}` }
}

function layoutFlow(nodes, edges) {
  const positions = new Map()
  const adj = new Map()
  const inDeg = new Map()
  nodes.forEach(n => { adj.set(n.id, []); inDeg.set(n.id, 0) })
  edges.forEach(e => {
    const from = e.from || e.from_node, to = e.to || e.to_node
    if (adj.has(from) && inDeg.has(to)) { adj.get(from).push(to); inDeg.set(to, inDeg.get(to) + 1) }
  })
  const sorted = []
  const queue = [...inDeg.entries()].filter(([, d]) => d === 0).map(([id]) => id)
  while (queue.length) {
    const id = queue.shift(); sorted.push(id)
    for (const next of (adj.get(id) || [])) { inDeg.set(next, inDeg.get(next) - 1); if (inDeg.get(next) === 0) queue.push(next) }
  }
  nodes.forEach(n => { if (!sorted.includes(n.id)) sorted.push(n.id) })
  const perRow = 4
  sorted.forEach((id, i) => { positions.set(id, { x: 100 + (i % perRow) * (NODE_WIDTH + 50), y: 60 + Math.floor(i / perRow) * 120 }) })
  const maxRow = Math.ceil(sorted.length / perRow)
  return { positions, viewBox: `0 0 ${Math.max(800, perRow * (NODE_WIDTH + 50) + 100)} ${maxRow * 120 + 100}` }
}

function layoutTimeline(nodes, edges) {
  const positions = new Map()
  const fromMap = new Map()
  edges.forEach(e => { fromMap.set(e.from || e.from_node, e.to || e.to_node) })
  const targets = new Set(edges.map(e => e.to || e.to_node))
  let start = nodes.find(n => !targets.has(n.id)) || nodes[0]
  const visited = new Set(); const ordered = []
  let current = start?.id
  while (current && !visited.has(current)) { visited.add(current); ordered.push(current); current = fromMap.get(current) }
  nodes.forEach(n => { if (!visited.has(n.id)) ordered.push(n.id) })
  ordered.forEach((id, i) => { positions.set(id, { x: 400, y: 60 + i * 110 }) })
  return { positions, viewBox: `0 0 800 ${ordered.length * 110 + 80}` }
}

function layoutCycle(nodes, edges) {
  const positions = new Map()
  const fromMap = new Map()
  edges.forEach(e => { fromMap.set(e.from || e.from_node, e.to || e.to_node) })
  const ordered = []; const visited = new Set()
  let current = nodes[0]?.id
  while (current && !visited.has(current)) { visited.add(current); ordered.push(current); current = fromMap.get(current) }
  nodes.forEach(n => { if (!visited.has(n.id)) ordered.push(n.id) })
  const cx = 400, cy = 300, rx = 250, ry = 200, count = ordered.length
  ordered.forEach((id, i) => {
    const angle = -Math.PI / 2 + (2 * Math.PI * i) / count
    positions.set(id, { x: cx + rx * Math.cos(angle), y: cy + ry * Math.sin(angle) })
  })
  return { positions, viewBox: '0 0 800 600' }
}

function layoutMindmap(nodes, edges) {
  const positions = new Map()
  const levels = new Map()
  nodes.forEach(n => { const lvl = n.level || 0; if (!levels.has(lvl)) levels.set(lvl, []); levels.get(lvl).push(n) })
  const cx = 400, cy = 300
  ;(levels.get(0) || [nodes[0]]).forEach(n => { if (n) positions.set(n.id, { x: cx, y: cy }) })
  const l1 = levels.get(1) || []
  l1.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / Math.max(l1.length, 1) - Math.PI / 2
    positions.set(n.id, { x: cx + 220 * Math.cos(angle), y: cy + 220 * Math.sin(angle) })
  })
  const parentEdges = new Map()
  edges.forEach(e => { const to = e.to || e.to_node; if (!parentEdges.has(to)) parentEdges.set(to, e.from || e.from_node) })
  for (let lvl = 2; lvl <= 5; lvl++) {
    (levels.get(lvl) || []).forEach((n, i) => {
      const parentPos = positions.get(parentEdges.get(n.id)) || { x: cx, y: cy }
      const angle = Math.atan2(parentPos.y - cy, parentPos.x - cx)
      const spread = (i - ((levels.get(lvl) || []).length - 1) / 2) * 0.4
      positions.set(n.id, { x: parentPos.x + 100 * Math.cos(angle + spread), y: parentPos.y + 100 * Math.sin(angle + spread) })
    })
  }
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
  positions.forEach(p => { minX = Math.min(minX, p.x - NODE_WIDTH / 2); maxX = Math.max(maxX, p.x + NODE_WIDTH / 2); minY = Math.min(minY, p.y - NODE_HEIGHT / 2); maxY = Math.max(maxY, p.y + NODE_HEIGHT / 2) })
  const pad = 60
  return { positions, viewBox: `${minX - pad} ${minY - pad} ${Math.max(800, maxX - minX + pad * 2)} ${Math.max(600, maxY - minY + pad * 2)}` }
}

const LAYOUT_FNS = { tree: layoutTree, flow: layoutFlow, timeline: layoutTimeline, cycle: layoutCycle, mindmap: layoutMindmap }

/* ─── Edge geometry ─── */

function getRectEdgePoint(center, target, halfW, halfH) {
  const dx = target.x - center.x, dy = target.y - center.y
  if (dx === 0 && dy === 0) return { x: center.x, y: center.y + halfH }
  const scale = Math.abs(dx) / halfW > Math.abs(dy) / halfH ? halfW / Math.abs(dx) : halfH / Math.abs(dy)
  return { x: center.x + dx * scale, y: center.y + dy * scale }
}

function computeQuadBezier(from, to) {
  const dx = to.x - from.x, dy = to.y - from.y
  const dist = Math.sqrt(dx * dx + dy * dy)
  const curvature = Math.min(dist * 0.15, 30)
  const midX = (from.x + to.x) / 2, midY = (from.y + to.y) / 2
  const nx = -dy / (dist || 1), ny = dx / (dist || 1)
  return { cx: midX + nx * curvature, cy: midY + ny * curvature }
}

/* ─── Type mini-icons for SVG ─── */
const TYPE_ICONS = {
  concept:  'M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25',
  process:  'M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z',
  example:  'M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18',
  category: 'M2.25 7.125C2.25 6.504 2.754 6 3.375 6h6c.621 0 1.125.504 1.125 1.125v3.75c0 .621-.504 1.125-1.125 1.125h-6a1.125 1.125 0 01-1.125-1.125v-3.75zM14.25 8.625c0-.621.504-1.125 1.125-1.125h5.25c.621 0 1.125.504 1.125 1.125v8.25c0 .621-.504 1.125-1.125 1.125h-5.25a1.125 1.125 0 01-1.125-1.125v-8.25zM3.75 16.125c0-.621.504-1.125 1.125-1.125h5.25c.621 0 1.125.504 1.125 1.125v2.25c0 .621-.504 1.125-1.125 1.125h-5.25a1.125 1.125 0 01-1.125-1.125v-2.25z',
  outcome:  'M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
}

/* ═══════════════════════════════════════ */

export default function ConceptDiagram({ diagram, compact = false, className = '' }) {
  const [selectedNode, setSelectedNode] = useState(null)

  const { positions, viewBox } = useMemo(() => {
    if (!diagram?.nodes?.length) return { positions: new Map(), viewBox: '0 0 800 600' }
    return (LAYOUT_FNS[diagram.diagram_type] || layoutTree)(diagram.nodes, diagram.edges || [])
  }, [diagram])

  if (!diagram?.nodes?.length) return null

  const nodeMap = new Map(diagram.nodes.map(n => [n.id, n]))
  const scale = compact ? COMPACT_SCALE : 1
  const halfW = (NODE_WIDTH / 2) * scale
  const halfH = (NODE_HEIGHT / 2) * scale
  const selectedData = selectedNode ? nodeMap.get(selectedNode) : null
  const selectedColors = selectedData ? (NODE_COLORS[selectedData.type] || NODE_COLORS.concept) : null

  // Parse viewBox for atmosphere orbs
  const vbParts = viewBox.split(' ').map(Number)
  const vbW = vbParts[2] || 800
  const vbH = vbParts[3] || 600

  return (
    <div className={`${className}`}>

      {/* ─── Header ─── */}
      {!compact && (
        <div className="flex items-start justify-between mb-4 animate-fade-up">
          <div className="flex-1 min-w-0">
            <h3 className="font-display text-[17px] font-bold text-navy-900 leading-tight mb-0.5">{diagram.title}</h3>
            <p className="text-[12px] text-surface-400 leading-relaxed">{diagram.summary}</p>
          </div>
          <span className="ml-3 flex-shrink-0 px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-navy-800/[0.06] text-navy-600 border border-navy-200/40">
            {diagram.diagram_type}
          </span>
        </div>
      )}

      {/* ─── SVG Canvas ─── */}
      <div className={`rounded-2xl border border-surface-200/80 overflow-hidden relative ${compact ? 'bg-white' : 'bg-surface-50/50'} animate-fade-up`}
        style={compact ? {} : { animationDelay: '0.06s' }}>

        {/* Atmosphere orbs (non-compact only) */}
        {!compact && (
          <>
            <div className="absolute top-6 right-10 w-40 h-40 rounded-full bg-navy-100/20 blur-3xl pointer-events-none" />
            <div className="absolute bottom-6 left-8 w-32 h-32 rounded-full bg-amber-100/20 blur-3xl pointer-events-none" />
          </>
        )}

        <svg
          viewBox={viewBox}
          className="w-full h-auto relative z-[1]"
          style={{ maxHeight: compact ? '360px' : '520px' }}
          role="img"
          aria-label={`Concept diagram: ${diagram.title}`}
        >
          <defs>
            {/* Subtle grid pattern for canvas depth */}
            <pattern id="diagram-grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <circle cx="20" cy="20" r="0.5" fill="#d1d5e0" opacity="0.4" />
            </pattern>

            {/* Arrowheads using navy tones */}
            <marker id="arrow-solid" viewBox="0 0 10 7" refX="10" refY="3.5" markerWidth="8" markerHeight="6" orient="auto-start-reverse">
              <polygon points="0 0, 10 3.5, 0 7" fill="#9ba2b5" />
            </marker>
            <marker id="arrow-bold" viewBox="0 0 10 7" refX="10" refY="3.5" markerWidth="9" markerHeight="7" orient="auto-start-reverse">
              <polygon points="0 0, 10 3.5, 0 7" fill="#1e3a8a" />
            </marker>
            <marker id="arrow-dashed" viewBox="0 0 10 7" refX="10" refY="3.5" markerWidth="7" markerHeight="5" orient="auto-start-reverse">
              <polygon points="0 0, 10 3.5, 0 7" fill="#d1d5e0" />
            </marker>

            {/* Node drop shadow */}
            <filter id="node-shadow" x="-8%" y="-8%" width="116%" height="132%">
              <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#1e3a8a" floodOpacity="0.06" />
            </filter>
            <filter id="node-shadow-active" x="-12%" y="-12%" width="124%" height="140%">
              <feDropShadow dx="0" dy="3" stdDeviation="6" floodColor="#1e3a8a" floodOpacity="0.12" />
            </filter>
          </defs>

          {/* Background grid */}
          <rect x={vbParts[0] || 0} y={vbParts[1] || 0} width={vbW} height={vbH} fill="url(#diagram-grid)" />

          {/* ─── Edges ─── */}
          {(diagram.edges || []).map((edge, i) => {
            const fromId = edge.from || edge.from_node, toId = edge.to || edge.to_node
            const fromPos = positions.get(fromId), toPos = positions.get(toId)
            if (!fromPos || !toPos) return null
            const fromPt = getRectEdgePoint(fromPos, toPos, halfW, halfH)
            const toPt = getRectEdgePoint(toPos, fromPos, halfW, halfH)
            const { cx, cy } = computeQuadBezier(fromPt, toPt)

            const style = edge.style || 'solid'
            const strokeProps = {
              solid:  { stroke: '#9ba2b5', strokeWidth: 1.5, strokeDasharray: 'none', markerEnd: 'url(#arrow-solid)' },
              dashed: { stroke: '#d1d5e0', strokeWidth: 1.5, strokeDasharray: '6 4', markerEnd: 'url(#arrow-dashed)' },
              bold:   { stroke: '#1e3a8a', strokeWidth: 2.5, strokeDasharray: 'none', markerEnd: 'url(#arrow-bold)' },
            }[style] || { stroke: '#9ba2b5', strokeWidth: 1.5, strokeDasharray: 'none', markerEnd: 'url(#arrow-solid)' }

            const labelX = (fromPt.x + 2 * cx + toPt.x) / 4 + (toPt.x - fromPt.x) * 0.25
            const labelY = (fromPt.y + 2 * cy + toPt.y) / 4 + (toPt.y - fromPt.y) * 0.25

            return (
              <g key={`edge-${i}`} opacity={0.85}>
                <path d={`M ${fromPt.x} ${fromPt.y} Q ${cx} ${cy} ${toPt.x} ${toPt.y}`} fill="none" {...strokeProps} />
                {edge.label && (
                  <>
                    <rect x={labelX - edge.label.length * 3.2} y={labelY - 9} width={edge.label.length * 6.4} height={18}
                      rx={6} fill="white" stroke="#e5e7ee" strokeWidth={0.8} />
                    <text x={labelX} y={labelY + 3.5} textAnchor="middle" fill="#9ba2b5" fontSize={10} fontWeight={600}
                      fontFamily="'Plus Jakarta Sans', system-ui, sans-serif">{edge.label}</text>
                  </>
                )}
              </g>
            )
          })}

          {/* ─── Nodes ─── */}
          {diagram.nodes.map((node, nodeIdx) => {
            const pos = positions.get(node.id)
            if (!pos) return null
            const colors = NODE_COLORS[node.type] || NODE_COLORS.concept
            const isSelected = selectedNode === node.id
            const w = NODE_WIDTH * scale, h = NODE_HEIGHT * scale
            const iconPath = TYPE_ICONS[node.type] || TYPE_ICONS.concept
            const iconSize = compact ? 10 : 12

            return (
              <g key={node.id} role="button" tabIndex={0}
                aria-label={`${node.type}: ${node.label}. ${node.detail}`}
                onClick={() => setSelectedNode(isSelected ? null : node.id)}
                onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSelectedNode(isSelected ? null : node.id) } }}
                style={{ cursor: 'pointer' }}
              >
                {/* Selection glow ring */}
                {isSelected && (
                  <rect x={pos.x - w / 2 - 4} y={pos.y - h / 2 - 4} width={w + 8} height={h + 8}
                    rx={16} fill="none" stroke={colors.badge} strokeWidth={2} opacity={0.3}>
                    <animate attributeName="opacity" values="0.3;0.15;0.3" dur="2s" repeatCount="indefinite" />
                  </rect>
                )}

                {/* Node card */}
                <rect x={pos.x - w / 2} y={pos.y - h / 2} width={w} height={h}
                  rx={12} fill="white"
                  stroke={isSelected ? colors.badge : '#e5e7ee'}
                  strokeWidth={isSelected ? 1.5 : 0.8}
                  filter={isSelected ? 'url(#node-shadow-active)' : 'url(#node-shadow)'} />

                {/* Left accent bar */}
                <rect x={pos.x - w / 2} y={pos.y - h / 2} width={4} height={h}
                  rx={2} fill={colors.badge} opacity={isSelected ? 1 : 0.7} />

                {/* Tinted background fill (subtle) */}
                <rect x={pos.x - w / 2 + 4} y={pos.y - h / 2 + 0.8} width={w - 4.8} height={h - 1.6}
                  rx={10} fill={colors.fill} opacity={0.5} />

                {/* Type icon */}
                <g transform={`translate(${pos.x - w / 2 + 14}, ${pos.y - iconSize / 2}) scale(${iconSize / 24})`}>
                  <path d={iconPath} fill="none" stroke={colors.badge} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity={0.6} />
                </g>

                {/* Label */}
                <text x={pos.x + 6} y={pos.y + 1} textAnchor="middle" dominantBaseline="middle"
                  fill={colors.text} fontSize={compact ? 11 : 12} fontWeight={600}
                  fontFamily="'Plus Jakarta Sans', system-ui, sans-serif">
                  {node.label.length > 20 ? node.label.slice(0, 18) + '\u2026' : node.label}
                </text>
              </g>
            )
          })}
        </svg>
      </div>

      {/* ─── Detail Panel ─── */}
      {selectedData && (
        <div className="mt-3 rounded-xl border border-surface-200/80 bg-white p-4 animate-fade-up relative overflow-hidden"
          role="region" aria-label={`Details for ${selectedData.label}`}>
          {/* Accent left border */}
          <div className="absolute left-0 top-0 bottom-0 w-[3px] rounded-l-xl" style={{ backgroundColor: selectedColors.badge }} />

          <div className="flex items-center gap-2.5 mb-2 pl-2">
            <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${selectedColors.tagBg} ${selectedColors.tagText} border ${selectedColors.tagBorder}`}>
              {selectedData.type}
            </span>
            <h4 className="text-[14px] font-bold text-navy-900">{selectedData.label}</h4>
          </div>
          <p className="text-[13px] text-surface-400 leading-relaxed pl-2">{selectedData.detail}</p>
        </div>
      )}

      {/* ─── Legend ─── */}
      {!compact && (
        <div className="mt-3 flex items-center gap-2 flex-wrap animate-fade-up" style={{ animationDelay: '0.12s' }}>
          <span className="text-[10px] text-surface-300 font-medium mr-1">Legend</span>
          {Object.entries(NODE_COLORS).map(([type, colors]) => (
            <button key={type}
              onClick={() => {
                const firstOfType = diagram.nodes.find(n => n.type === type)
                if (firstOfType) setSelectedNode(prev => prev === firstOfType.id ? null : firstOfType.id)
              }}
              className={`flex items-center gap-1.5 px-2 py-1 rounded-lg border transition-all hover:shadow-sm ${colors.tagBg} ${colors.tagBorder} cursor-pointer`}>
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: colors.badge }} />
              <span className={`text-[10px] font-semibold capitalize ${colors.tagText}`}>{type}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
