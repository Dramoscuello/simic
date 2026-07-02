<template>
  <g :transform="`translate(${x}, ${y}) scale(${scale})`">
    
    <!-- ========================== -->
    <!-- TIPO: WARNING (Triángulo Amarillo) -->
    <!-- ========================== -->
    <g v-if="type === 'warning'">
      <polygon points="110,20 200,180 20,180" fill="rgba(0,0,0,0.15)" transform="translate(5,5)"/>
      <polygon points="110,15 205,185 15,185" fill="#f1c40f" stroke="#d4a800" stroke-width="4" stroke-linejoin="round"/>
      <polygon points="110,35 185,170 35,170" fill="none" stroke="#333" stroke-width="2" stroke-linejoin="round"/>
      <line x1="110" y1="70" x2="110" y2="120" stroke="#333" stroke-width="10" stroke-linecap="round"/>
      <circle cx="110" cy="145" r="6" fill="#333"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: PROHIBITED (Círculo prohibido) -->
    <!-- ========================== -->
    <g v-if="type === 'prohibited'" transform="translate(10, 0)"> 
      <circle cx="104" cy="104" r="85" fill="rgba(0,0,0,0.15)"/>
      <circle cx="100" cy="100" r="85" fill="#ffffff"/>
      <circle cx="100" cy="100" r="80" fill="none" stroke="#c0392b" stroke-width="15"/>
      <line x1="40" y1="40" x2="160" y2="160" stroke="#c0392b" stroke-width="15" stroke-linecap="round"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: INFO (Círculo azul "i") -->
    <!-- ========================== -->
    <g v-if="type === 'info'" transform="translate(10, 0)">
      <circle cx="104" cy="104" r="85" fill="rgba(0,0,0,0.15)"/>
      <circle cx="100" cy="100" r="85" fill="#3498db"/>
      <circle cx="100" cy="100" r="85" fill="none" stroke="#2980b9" stroke-width="4"/>
      <circle cx="100" cy="60" r="10" fill="#ffffff"/>
      <line x1="100" y1="85" x2="100" y2="150" stroke="#ffffff" stroke-width="18" stroke-linecap="round"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: SALE -->
    <!-- ========================== -->
    <g v-if="type === 'sale'" transform="translate(10, 0)">
      <circle cx="104" cy="104" r="85" fill="rgba(0,0,0,0.15)"/>
      <circle cx="100" cy="100" r="85" fill="#e74c3c"/>
      <circle cx="100" cy="100" r="85" fill="none" stroke="#c0392b" stroke-width="4"/>
      <polygon points="100,20 110,45 140,45 118,62 128,90 100,72 72,90 82,62 60,45 90,45" fill="#f1c40f" transform="translate(0,-5) scale(0.9) translate(11,11)"/>
      <text x="100" y="95" text-anchor="middle" font-family="Arial, sans-serif" font-size="32" font-weight="bold" fill="#ffffff">SALE</text>
      <text x="100" y="130" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" font-weight="bold" fill="#ffffff">% OFF</text>
    </g>

    <!-- ========================== -->
    <!-- TIPO: FOOD -->
    <!-- ========================== -->
    <g v-if="type === 'food'" transform="translate(10, 0)">
      <ellipse cx="104" cy="150" rx="70" ry="20" fill="rgba(0,0,0,0.1)"/>
      <ellipse cx="100" cy="140" rx="65" ry="18" fill="#ecf0f1" stroke="#bdc3c7" stroke-width="3"/>
      <ellipse cx="100" cy="135" rx="55" ry="14" fill="none" stroke="#bdc3c7" stroke-width="2"/>
      <path d="M35 135 Q35 60 100 50 Q165 60 165 135" fill="#bdc3c7" stroke="#95a5a6" stroke-width="3"/>
      <path d="M55 110 Q60 80 85 70" fill="none" stroke="#ecf0f1" stroke-width="4" stroke-linecap="round"/>
      <ellipse cx="100" cy="48" rx="12" ry="8" fill="#95a5a6" stroke="#7f8c8d" stroke-width="2"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: NO FOOD -->
    <!-- ========================== -->
    <g v-if="type === 'noFood'" transform="translate(10, 0)">
      <circle cx="104" cy="104" r="85" fill="rgba(0,0,0,0.15)"/>
      <circle cx="100" cy="100" r="85" fill="#ffffff"/>
      <ellipse cx="100" cy="115" rx="40" ry="12" fill="#ecf0f1" stroke="#bdc3c7" stroke-width="2"/>
      <path d="M60 115 Q60 70 100 62 Q140 70 140 115" fill="#bdc3c7" stroke="#95a5a6" stroke-width="2"/>
      <ellipse cx="100" cy="60" rx="8" ry="5" fill="#95a5a6"/>
      <circle cx="100" cy="100" r="80" fill="none" stroke="#c0392b" stroke-width="8"/>
      <line x1="40" y1="40" x2="160" y2="160" stroke="#c0392b" stroke-width="8" stroke-linecap="round"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: PARKING -->
    <!-- ========================== -->
    <g v-if="type === 'parking'" transform="translate(10, 0)">
      <rect x="19" y="19" width="170" height="170" rx="12" fill="rgba(0,0,0,0.15)"/>
      <rect x="15" y="15" width="170" height="170" rx="12" fill="#3498db"/>
      <rect x="15" y="15" width="170" height="170" rx="12" fill="none" stroke="#2980b9" stroke-width="4"/>
      <text x="100" y="135" text-anchor="middle" font-family="Arial, sans-serif" font-size="120" font-weight="bold" fill="#ffffff">P</text>
    </g>

    <!-- ========================== -->
    <!-- TIPO: NO PARKING -->
    <!-- ========================== -->
    <g v-if="type === 'noParking'" transform="translate(10, 0)">
      <circle cx="104" cy="104" r="85" fill="rgba(0,0,0,0.15)"/>
      <circle cx="100" cy="100" r="85" fill="#3498db"/>
      <text x="100" y="125" text-anchor="middle" font-family="Arial, sans-serif" font-size="90" font-weight="bold" fill="#ffffff">P</text>
      <circle cx="100" cy="100" r="80" fill="none" stroke="#c0392b" stroke-width="8"/>
      <line x1="35" y1="35" x2="165" y2="165" stroke="#c0392b" stroke-width="8" stroke-linecap="round"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: EXIT -->
    <!-- ========================== -->
    <g v-if="type === 'exit'" transform="translate(-30, 20)"> 
        <!-- Exit es más ancho (280x160), lo ajustamos un poco -->
      <rect x="14" y="14" width="250" height="130" rx="6" fill="rgba(0,0,0,0.15)"/>
      <rect x="10" y="10" width="250" height="130" rx="6" fill="#27ae60"/>
      <rect x="10" y="10" width="250" height="130" rx="6" fill="none" stroke="#1e8449" stroke-width="4"/>
      <g transform="translate(50, 75)">
        <rect x="-20" y="-40" width="30" height="60" fill="none" stroke="#ffffff" stroke-width="3"/>
        <circle cx="20" cy="-25" r="8" fill="#ffffff"/>
        <line x1="20" y1="-17" x2="20" y2="5" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>
        <line x1="20" y1="-10" x2="8" y2="0" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>
        <line x1="20" y1="-10" x2="32" y2="0" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>
        <line x1="20" y1="5" x2="10" y2="20" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>
        <line x1="20" y1="5" x2="30" y2="20" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>
      </g>
      <g transform="translate(160, 75)">
        <line x1="0" y1="0" x2="60" y2="0" stroke="#ffffff" stroke-width="6" stroke-linecap="round"/>
        <polyline points="45,-15 60,0 45,15" fill="none" stroke="#ffffff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
      </g>
      <text x="185" y="125" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#ffffff">EXIT</text>
    </g>

    <!-- ========================== -->
    <!-- TIPO: WIFI -->
    <!-- ========================== -->
    <g v-if="type === 'wifi'" transform="translate(10, 0)">
      <circle cx="104" cy="104" r="85" fill="rgba(0,0,0,0.15)"/>
      <circle cx="100" cy="100" r="85" fill="#3498db"/>
      <circle cx="100" cy="100" r="85" fill="none" stroke="#2980b9" stroke-width="4"/>
      <path d="M30 95 Q100 40 170 95" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round"/>
      <path d="M50 115 Q100 70 150 115" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round"/>
      <path d="M70 135 Q100 100 130 135" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round"/>
      <circle cx="100" cy="155" r="10" fill="#ffffff"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: CAMERA -->
    <!-- ========================== -->
    <g v-if="type === 'camera'" transform="translate(10, 0)">
      <rect x="24" y="69" width="160" height="100" rx="12" fill="rgba(0,0,0,0.1)"/>
      <rect x="20" y="65" width="160" height="100" rx="12" fill="#2c3e50" stroke="#1a252f" stroke-width="3"/>
      <rect x="70" y="45" width="40" height="20" rx="4" fill="#2c3e50" stroke="#1a252f" stroke-width="3"/>
      <circle cx="100" cy="115" r="38" fill="#1a252f"/>
      <circle cx="100" cy="115" r="30" fill="#34495e"/>
      <circle cx="100" cy="115" r="20" fill="#2c3e50"/>
      <circle cx="92" cy="107" r="8" fill="#4a6785" opacity="0.6"/>
      <circle cx="155" cy="55" r="8" fill="#e74c3c"/>
      <rect x="140" y="75" width="25" height="15" rx="2" fill="#f1c40f"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: PHONE -->
    <!-- ========================== -->
    <g v-if="type === 'phone'" transform="translate(10, 0)">
      <rect x="59" y="19" width="90" height="170" rx="12" fill="rgba(0,0,0,0.1)"/>
      <rect x="55" y="15" width="90" height="170" rx="12" fill="#2c3e50" stroke="#1a252f" stroke-width="3"/>
      <rect x="65" y="40" width="70" height="110" rx="4" fill="#3498db"/>
      <rect x="85" y="25" width="30" height="6" rx="3" fill="#1a252f"/>
      <circle cx="75" cy="28" r="4" fill="#1a252f"/>
      <circle cx="100" cy="167" r="12" fill="none" stroke="#1a252f" stroke-width="2"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: NO PHONE -->
    <!-- ========================== -->
    <g v-if="type === 'noPhone'" transform="translate(10, 0)">
      <circle cx="104" cy="104" r="85" fill="rgba(0,0,0,0.15)"/>
      <circle cx="100" cy="100" r="85" fill="#ffffff"/>
      <rect x="70" y="35" width="60" height="110" rx="8" fill="#2c3e50"/>
      <rect x="78" y="50" width="44" height="70" rx="2" fill="#5d6d7e"/>
      <circle cx="100" cy="132" r="6" fill="#1a252f"/>
      <circle cx="100" cy="100" r="80" fill="none" stroke="#c0392b" stroke-width="8"/>
      <line x1="40" y1="40" x2="160" y2="160" stroke="#c0392b" stroke-width="8" stroke-linecap="round"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: SMOKING -->
    <!-- ========================== -->
    <g v-if="type === 'smoking'" transform="translate(10, 20)"> 
        <!-- Ajustamos posición vertical -->
      <rect x="14" y="94" width="150" height="35" rx="4" fill="rgba(0,0,0,0.1)"/>
      <rect x="10" y="90" width="40" height="30" rx="2" fill="#e67e22"/>
      <rect x="10" y="90" width="40" height="30" rx="2" fill="none" stroke="#d35400" stroke-width="2"/>
      <rect x="50" y="90" width="100" height="30" rx="2" fill="#ffffff"/>
      <rect x="50" y="90" width="100" height="30" rx="2" fill="none" stroke="#bdc3c7" stroke-width="2"/>
      <rect x="145" y="90" width="15" height="30" fill="#e74c3c"/>
      <path d="M155 85 Q165 70 155 55 Q145 40 155 25" fill="none" stroke="#95a5a6" stroke-width="4" stroke-linecap="round"/>
      <path d="M165 80 Q175 60 165 45 Q155 30 165 15" fill="none" stroke="#bdc3c7" stroke-width="3" stroke-linecap="round"/>
      <path d="M175 85 Q185 65 175 50 Q165 35 175 20" fill="none" stroke="#95a5a6" stroke-width="2" stroke-linecap="round"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: NO SMOKING -->
    <!-- ========================== -->
    <g v-if="type === 'noSmoking'" transform="translate(10, 0)">
      <circle cx="104" cy="104" r="85" fill="rgba(0,0,0,0.15)"/>
      <circle cx="100" cy="100" r="85" fill="#ffffff"/>
      <rect x="35" y="90" width="30" height="20" rx="2" fill="#e67e22"/>
      <rect x="65" y="90" width="80" height="20" fill="#f5f5f5" stroke="#ccc" stroke-width="1"/>
      <rect x="140" y="90" width="12" height="20" fill="#e74c3c"/>
      <path d="M148 85 Q155 70 148 60" fill="none" stroke="#aaa" stroke-width="3" stroke-linecap="round"/>
      <circle cx="100" cy="100" r="80" fill="none" stroke="#c0392b" stroke-width="8"/>
      <line x1="40" y1="40" x2="160" y2="160" stroke="#c0392b" stroke-width="8" stroke-linecap="round"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: PETS -->
    <!-- ========================== -->
    <g v-if="type === 'pets'" transform="translate(10, 0)">
      <ellipse cx="104" cy="180" rx="50" ry="10" fill="rgba(0,0,0,0.1)"/>
      <ellipse cx="100" cy="130" rx="45" ry="35" fill="#8B4513"/>
      <circle cx="100" cy="70" r="35" fill="#8B4513"/>
      <ellipse cx="60" cy="50" rx="15" ry="25" fill="#6d3610" transform="rotate(-20 60 50)"/>
      <ellipse cx="140" cy="50" rx="15" ry="25" fill="#6d3610" transform="rotate(20 140 50)"/>
      <ellipse cx="100" cy="85" rx="18" ry="12" fill="#d4a574"/>
      <ellipse cx="100" cy="80" rx="8" ry="6" fill="#333"/>
      <circle cx="82" cy="62" r="6" fill="#333"/>
      <circle cx="118" cy="62" r="6" fill="#333"/>
      <circle cx="84" cy="60" r="2" fill="#fff"/>
      <circle cx="120" cy="60" r="2" fill="#fff"/>
      <ellipse cx="70" cy="170" rx="12" ry="8" fill="#8B4513"/>
      <ellipse cx="130" cy="170" rx="12" ry="8" fill="#8B4513"/>
      <path d="M145 130 Q170 110 165 85" fill="none" stroke="#8B4513" stroke-width="12" stroke-linecap="round"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: NO PETS -->
    <!-- ========================== -->
    <g v-if="type === 'noPets'" transform="translate(10, 0)">
      <circle cx="104" cy="104" r="85" fill="rgba(0,0,0,0.15)"/>
      <circle cx="100" cy="100" r="85" fill="#ffffff"/>
      <ellipse cx="100" cy="115" rx="30" ry="22" fill="#8B4513"/>
      <circle cx="100" cy="70" r="25" fill="#8B4513"/>
      <ellipse cx="75" cy="55" rx="10" ry="16" fill="#6d3610" transform="rotate(-15 75 55)"/>
      <ellipse cx="125" cy="55" rx="10" ry="16" fill="#6d3610" transform="rotate(15 125 55)"/>
      <ellipse cx="100" cy="80" rx="12" ry="8" fill="#d4a574"/>
      <ellipse cx="100" cy="77" rx="5" ry="4" fill="#333"/>
      <circle cx="90" cy="65" r="4" fill="#333"/>
      <circle cx="110" cy="65" r="4" fill="#333"/>
      <ellipse cx="80" cy="140" rx="8" ry="5" fill="#8B4513"/>
      <ellipse cx="120" cy="140" rx="8" ry="5" fill="#8B4513"/>
      <circle cx="100" cy="100" r="80" fill="none" stroke="#c0392b" stroke-width="8"/>
      <line x1="40" y1="40" x2="160" y2="160" stroke="#c0392b" stroke-width="8" stroke-linecap="round"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: ARROW -->
    <!-- ========================== -->
    <g v-if="type === 'arrow'" transform="translate(10, 40)"> 
        <!-- Ajuste vertical -->
      <polygon points="14,64 54,24 54,44 184,44 184,84 54,84 54,104" fill="rgba(0,0,0,0.15)"/>
      <polygon points="10,60 50,20 50,40 180,40 180,80 50,80 50,100" fill="#2c3e50" stroke="#1a252f" stroke-width="3" stroke-linejoin="round"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: ARROW UP -->
    <!-- ========================== -->
    <g v-if="type === 'arrowUp'" transform="translate(50, 0)"> 
        <!-- Centrado -->
      <polygon points="64,14 104,54 84,54 84,184 44,184 44,54 24,54" fill="rgba(0,0,0,0.15)"/>
      <polygon points="60,10 100,50 80,50 80,180 40,180 40,50 20,50" fill="#27ae60" stroke="#1e8449" stroke-width="3" stroke-linejoin="round"/>
    </g>
    
    <!-- ========================== -->
    <!-- TIPO: TRASH -->
    <!-- ========================== -->
    <g v-if="type === 'trash'" transform="translate(10, 0)">
      <path d="M54,64 L64,184 L144,184 L154,64" fill="rgba(0,0,0,0.1)"/>
      <rect x="35" y="40" width="130" height="15" rx="3" fill="#7f8c8d"/>
      <rect x="75" y="25" width="50" height="18" rx="3" fill="#95a5a6"/>
      <path d="M50,55 L60,180 L140,180 L150,55 Z" fill="#95a5a6" stroke="#7f8c8d" stroke-width="3"/>
      <line x1="75" y1="75" x2="72" y2="160" stroke="#7f8c8d" stroke-width="4" stroke-linecap="round"/>
      <line x1="100" y1="75" x2="100" y2="160" stroke="#7f8c8d" stroke-width="4" stroke-linecap="round"/>
      <line x1="125" y1="75" x2="128" y2="160" stroke="#7f8c8d" stroke-width="4" stroke-linecap="round"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: RECYCLE -->
    <!-- ========================== -->
    <g v-if="type === 'recycle'" transform="translate(10, 0)">
      <g transform="translate(100,100)">
        <path d="M-5,-70 L5,-70 L5,-30 L20,-30 L0,-5 L-20,-30 L-5,-30 Z" fill="#27ae60" transform="rotate(0)"/>
      </g>
      <g transform="translate(100,100)">
        <path d="M-5,-70 L5,-70 L5,-30 L20,-30 L0,-5 L-20,-30 L-5,-30 Z" fill="#27ae60" transform="rotate(120)"/>
      </g>
      <g transform="translate(100,100)">
        <path d="M-5,-70 L5,-70 L5,-30 L20,-30 L0,-5 L-20,-30 L-5,-30 Z" fill="#27ae60" transform="rotate(240)"/>
      </g>
      <path d="M95,35 Q130,50 130,90" fill="none" stroke="#27ae60" stroke-width="12" stroke-linecap="round"/>
      <path d="M130,110 Q120,150 85,155" fill="none" stroke="#27ae60" stroke-width="12" stroke-linecap="round"/>
      <path d="M70,145 Q40,130 40,90" fill="none" stroke="#27ae60" stroke-width="12" stroke-linecap="round"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: CLOCK -->
    <!-- ========================== -->
    <g v-if="type === 'clock'" transform="translate(10, 0)">
      <circle cx="104" cy="104" r="85" fill="rgba(0,0,0,0.1)"/>
      <circle cx="100" cy="100" r="85" fill="#ecf0f1" stroke="#bdc3c7" stroke-width="4"/>
      <circle cx="100" cy="100" r="75" fill="#ffffff" stroke="#95a5a6" stroke-width="2"/>
      <g stroke="#2c3e50" stroke-width="3">
        <line x1="100" y1="30" x2="100" y2="40"/>
        <line x1="100" y1="160" x2="100" y2="170"/>
        <line x1="30" y1="100" x2="40" y2="100"/>
        <line x1="160" y1="100" x2="170" y2="100"/>
        <line x1="150" y1="50" x2="143" y2="57" stroke-width="2"/>
        <line x1="150" y1="150" x2="143" y2="143" stroke-width="2"/>
        <line x1="50" y1="50" x2="57" y2="57" stroke-width="2"/>
        <line x1="50" y1="150" x2="57" y2="143" stroke-width="2"/>
      </g>
      <line x1="100" y1="100" x2="100" y2="55" stroke="#2c3e50" stroke-width="6" stroke-linecap="round"/>
      <!-- Minutero un poco diferente para no ser 12:00 -->
      <line x1="100" y1="100" x2="145" y2="75" stroke="#2c3e50" stroke-width="4" stroke-linecap="round"/>
      <circle cx="100" cy="100" r="6" fill="#e74c3c"/>
    </g>
    
    <!-- ========================== -->
    <!-- TIPO: MEDICAL -->
    <!-- ========================== -->
    <g v-if="type === 'medical'" transform="translate(10, 0)">
      <rect x="19" y="19" width="170" height="170" rx="20" fill="rgba(0,0,0,0.15)"/>
      <rect x="15" y="15" width="170" height="170" rx="20" fill="#ffffff" stroke="#e74c3c" stroke-width="4"/>
      <rect x="80" y="40" width="40" height="120" rx="4" fill="#e74c3c"/>
      <rect x="40" y="80" width="120" height="40" rx="4" fill="#e74c3c"/>
    </g>
    
    <!-- ========================== -->
    <!-- TIPO: ELEVATOR -->
    <!-- ========================== -->
    <g v-if="type === 'elevator'" transform="translate(10, 0)">
      <rect x="24" y="19" width="160" height="175" rx="8" fill="rgba(0,0,0,0.1)"/>
      <rect x="20" y="15" width="160" height="175" rx="8" fill="#2c3e50" stroke="#1a252f" stroke-width="3"/>
      <rect x="30" y="25" width="65" height="155" rx="2" fill="#5d6d7e"/>
      <rect x="88" y="85" width="5" height="30" rx="2" fill="#34495e"/>
      <rect x="105" y="25" width="65" height="155" rx="2" fill="#5d6d7e"/>
      <rect x="107" y="85" width="5" height="30" rx="2" fill="#34495e"/>
      <rect x="75" y="3" width="50" height="18" rx="3" fill="#2c3e50" stroke="#1a252f" stroke-width="2"/>
      <text x="100" y="16" text-anchor="middle" font-family="Arial" font-size="12" fill="#27ae60">▲ 3</text>
      <g transform="translate(60, 190)">
        <polygon points="0,0 10,-15 20,0" fill="#27ae60"/>
      </g>
      <g transform="translate(120, 175)">
        <polygon points="0,0 10,15 20,0" fill="#e74c3c"/>
      </g>
    </g>
    
    <!-- ========================== -->
    <!-- TIPO: STAIRS -->
    <!-- ========================== -->
    <g v-if="type === 'stairs'" transform="translate(10, 0)">
      <path d="M20,180 L20,150 L50,150 L50,120 L80,120 L80,90 L110,90 L110,60 L140,60 L140,30 L180,30 L180,180 Z" fill="#95a5a6" stroke="#7f8c8d" stroke-width="3" stroke-linejoin="round"/>
      <line x1="20" y1="150" x2="50" y2="150" stroke="#7f8c8d" stroke-width="2"/>
      <line x1="50" y1="120" x2="80" y2="120" stroke="#7f8c8d" stroke-width="2"/>
      <line x1="80" y1="90" x2="110" y2="90" stroke="#7f8c8d" stroke-width="2"/>
      <line x1="110" y1="60" x2="140" y2="60" stroke="#7f8c8d" stroke-width="2"/>
      <line x1="140" y1="30" x2="180" y2="30" stroke="#7f8c8d" stroke-width="2"/>
      <g transform="translate(85, 75)">
        <circle cx="0" cy="-25" r="10" fill="#2c3e50"/>
        <line x1="0" y1="-15" x2="0" y2="10" stroke="#2c3e50" stroke-width="4" stroke-linecap="round"/>
        <line x1="0" y1="-8" x2="-12" y2="0" stroke="#2c3e50" stroke-width="4" stroke-linecap="round"/>
        <line x1="0" y1="-8" x2="12" y2="-15" stroke="#2c3e50" stroke-width="4" stroke-linecap="round"/>
        <line x1="0" y1="10" x2="-10" y2="30" stroke="#2c3e50" stroke-width="4" stroke-linecap="round"/>
        <line x1="0" y1="10" x2="15" y2="15" stroke="#2c3e50" stroke-width="4" stroke-linecap="round"/>
      </g>
    </g>
    
    <!-- ========================== -->
    <!-- TIPO: WHEELCHAIR -->
    <!-- ========================== -->
    <g v-if="type === 'wheelchair'" transform="translate(10, 0)">
      <rect x="19" y="19" width="170" height="170" rx="12" fill="rgba(0,0,0,0.15)"/>
      <rect x="15" y="15" width="170" height="170" rx="12" fill="#3498db"/>
      <rect x="15" y="15" width="170" height="170" rx="12" fill="none" stroke="#2980b9" stroke-width="4"/>
      <circle cx="90" cy="50" r="18" fill="#ffffff"/>
      <line x1="90" y1="68" x2="90" y2="110" stroke="#ffffff" stroke-width="8" stroke-linecap="round"/>
      <line x1="90" y1="85" x2="120" y2="95" stroke="#ffffff" stroke-width="8" stroke-linecap="round"/>
      <path d="M90,110 L90,130 L120,130" fill="none" stroke="#ffffff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="90" cy="140" r="35" fill="none" stroke="#ffffff" stroke-width="8"/>
      <circle cx="145" cy="155" r="15" fill="none" stroke="#ffffff" stroke-width="6"/>
      <line x1="120" y1="130" x2="145" y2="155" stroke="#ffffff" stroke-width="6" stroke-linecap="round"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: RESTROOM -->
    <!-- ========================== -->
    <g v-if="type === 'restroom'" transform="translate(-30, 20)"> 
        <!-- Restroom es ancho (280) -->
      <rect x="10" y="10" width="260" height="180" rx="8" fill="#3498db" stroke="#2980b9" stroke-width="4"/>
      <line x1="140" y1="30" x2="140" y2="170" stroke="#ffffff" stroke-width="3"/>
      <g transform="translate(75, 100)">
        <circle cx="0" cy="-45" r="18" fill="#ffffff"/>
        <line x1="0" y1="-27" x2="0" y2="15" stroke="#ffffff" stroke-width="10" stroke-linecap="round"/>
        <line x1="-25" y1="-10" x2="25" y2="-10" stroke="#ffffff" stroke-width="10" stroke-linecap="round"/>
        <line x1="0" y1="15" x2="-20" y2="55" stroke="#ffffff" stroke-width="10" stroke-linecap="round"/>
        <line x1="0" y1="15" x2="20" y2="55" stroke="#ffffff" stroke-width="10" stroke-linecap="round"/>
      </g>
      <g transform="translate(205, 100)">
        <circle cx="0" cy="-45" r="18" fill="#ffffff"/>
        <polygon points="0,-27 -30,55 30,55" fill="#ffffff"/>
        <line x1="-25" y1="-10" x2="25" y2="-10" stroke="#ffffff" stroke-width="10" stroke-linecap="round"/>
      </g>
    </g>

    <!-- ========================== -->
    <!-- TIPO: DANGER -->
    <!-- ========================== -->
    <g v-if="type === 'danger'">
      <polygon points="110,20 200,180 20,180" fill="rgba(0,0,0,0.15)" transform="translate(5,5)"/>
      <polygon points="110,15 205,185 15,185" fill="#e74c3c" stroke="#c0392b" stroke-width="4" stroke-linejoin="round"/>
      <polygon points="110,40 180,170 40,170" fill="none" stroke="#f1c40f" stroke-width="3" stroke-linejoin="round"/>
      <circle cx="110" cy="95" r="28" fill="#ffffff"/>
      <circle cx="98" cy="88" r="8" fill="#e74c3c"/>
      <circle cx="122" cy="88" r="8" fill="#e74c3c"/>
      <ellipse cx="110" cy="105" rx="5" ry="3" fill="#e74c3c"/>
      <line x1="80" y1="130" x2="140" y2="160" stroke="#ffffff" stroke-width="8" stroke-linecap="round"/>
      <line x1="140" y1="130" x2="80" y2="160" stroke="#ffffff" stroke-width="8" stroke-linecap="round"/>
    </g>

    <!-- ========================== -->
    <!-- TIPO: STOP -->
    <!-- ========================== -->
    <g v-if="type === 'stop'" transform="translate(10, 0)">
      <polygon points="62,18 142,18 182,58 182,142 142,182 62,182 22,142 22,58" fill="rgba(0,0,0,0.15)" transform="translate(4,4)"/>
      <polygon points="60,15 140,15 180,55 180,140 140,180 60,180 20,140 20,55" fill="#c0392b" stroke="#922b21" stroke-width="4"/>
      <polygon points="65,25 135,25 170,60 170,135 135,170 65,170 30,135 30,60" fill="none" stroke="#ffffff" stroke-width="3"/>
      <text x="100" y="115" text-anchor="middle" font-family="Arial, sans-serif" font-size="48" font-weight="bold" fill="#ffffff">STOP</text>
    </g>

    <!-- Label opcional debajo del signo -->
    <text
      v-if="label"
      x="110"
      y="225"
      font-family="sans-serif"
      font-size="16"
      font-weight="bold"
      fill="#374151"
      text-anchor="middle"
    >
      {{ label }}
    </text>

  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x: { type: Number, default: 0 },
  y: { type: Number, default: 0 },
  width: { type: Number, default: 220 }, // Ancho base aproximado
  type: { type: String, default: 'warning' },
  label: { type: String, default: '' }
});

// Calculamos escala basada en el ancho deseado vs 220 (referencia)
const scale = computed(() => {
  return props.width / 220;
});
</script>
