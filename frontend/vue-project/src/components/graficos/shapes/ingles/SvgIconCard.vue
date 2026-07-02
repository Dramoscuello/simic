<template>
  <g :transform="`translate(${x}, ${y}) scale(${scale})`">
    
    <!-- ============================================ -->
    <!--     FOOD (COMIDA)                           -->
    <!-- ============================================ -->

    <!-- CARD APPLE -->
    <g v-if="type === 'card-apple'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#3498db"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">A</text>
      <g transform="translate(60, 70)">
        <ellipse cx="0" cy="8" rx="28" ry="25" fill="#e74c3c"/>
        <ellipse cx="-12" cy="-2" rx="8" ry="12" fill="#ec7063" opacity="0.6"/>
        <path d="M0,-18 Q5,-25 3,-30" fill="none" stroke="#795548" stroke-width="3" stroke-linecap="round"/>
        <ellipse cx="8" cy="-22" rx="10" ry="5" fill="#27ae60" transform="rotate(30 8 -22)"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">apple</text>
    </g>

    <!-- CARD BANANA -->
    <g v-if="type === 'card-banana'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#3498db"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">B</text>
      <g transform="translate(60, 70)">
        <path d="M-25,20 Q-30,-10 -10,-25 Q10,-35 25,-20 Q30,-5 20,15 Q10,25 -5,25 Q-20,25 -25,20" 
              fill="#f1c40f" stroke="#d4a800" stroke-width="2"/>
        <circle cx="-22" cy="18" r="3" fill="#8B4513"/>
        <circle cx="22" cy="-18" r="3" fill="#8B4513"/>
        <path d="M-15,15 Q0,-5 15,-15" fill="none" stroke="#d4a800" stroke-width="1" opacity="0.5"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">banana</text>
    </g>

    <!-- CARD ORANGE -->
    <g v-if="type === 'card-orange'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#3498db"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">C</text>
      <g transform="translate(60, 70)">
        <circle cx="0" cy="5" r="28" fill="#e67e22"/>
        <!-- Gradiente simulado simple -->
        <circle cx="0" cy="5" r="28" fill="#d35400" opacity="0.1"/>
        <ellipse cx="-10" cy="-5" rx="10" ry="8" fill="#f39c12" opacity="0.5"/>
        <ellipse cx="5" cy="-25" rx="8" ry="4" fill="#27ae60" transform="rotate(-20 5 -25)"/>
        <rect x="-2" y="-28" width="4" height="8" rx="2" fill="#795548"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">orange</text>
    </g>

    <!-- ============================================ -->
    <!--     CLOTHING (ROPA)                         -->
    <!-- ============================================ -->

    <!-- CARD SHIRT -->
    <g v-if="type === 'card-shirt'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#e74c3c"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">A</text>
      <g transform="translate(60, 72)">
        <path d="M-25,-25 L-15,-25 L-8,-15 L-8,30 L-25,30 Z" fill="#3498db"/>
        <path d="M25,-25 L15,-25 L8,-15 L8,30 L25,30 Z" fill="#3498db"/>
        <rect x="-8" y="-15" width="16" height="45" fill="#3498db"/>
        <path d="M-8,-15 L0,-25 L8,-15" fill="#3498db" stroke="#2980b9" stroke-width="1"/>
        <path d="M-5,-18 L0,-10 L5,-18" fill="#ffffff"/>
        <path d="M-25,-25 L-35,-15 L-30,0 L-25,-5" fill="#3498db" stroke="#2980b9" stroke-width="1"/>
        <path d="M25,-25 L35,-15 L30,0 L25,-5" fill="#3498db" stroke="#2980b9" stroke-width="1"/>
        <circle cx="0" cy="0" r="2" fill="#2980b9"/>
        <circle cx="0" cy="10" r="2" fill="#2980b9"/>
        <circle cx="0" cy="20" r="2" fill="#2980b9"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">shirt</text>
    </g>

    <!-- CARD PANTS -->
    <g v-if="type === 'card-pants'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#e74c3c"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">B</text>
      <g transform="translate(60, 70)">
        <rect x="-28" y="-30" width="56" height="12" rx="2" fill="#2c3e50"/>
        <path d="M-28,-18 L-25,35 L-5,35 L-2,-18 Z" fill="#34495e"/>
        <path d="M2,-18 L5,35 L25,35 L28,-18 Z" fill="#34495e"/>
        <line x1="0" y1="-18" x2="0" y2="5" stroke="#7f8c8d" stroke-width="2"/>
        <path d="M-24,-15 L-20,-5 L-8,-5 L-8,-18" fill="none" stroke="#2c3e50" stroke-width="1"/>
        <path d="M24,-15 L20,-5 L8,-5 L8,-18" fill="none" stroke="#2c3e50" stroke-width="1"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">pants</text>
    </g>

    <!-- CARD SHOES -->
    <g v-if="type === 'card-shoes'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#e74c3c"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">C</text>
      <g transform="translate(60, 75)">
        <path d="M-35,15 L40,15 L40,20 Q30,25 -30,25 L-35,20 Z" fill="#2c3e50"/>
        <path d="M-30,15 Q-35,0 -25,-15 Q-15,-25 5,-25 L5,0 Q20,5 35,10 L35,15 Z" fill="#e74c3c"/>
        <path d="M-5,-25 L-5,-35 Q5,-40 15,-35 L15,-20" fill="#c0392b"/>
        <line x1="-5" y1="-15" x2="10" y2="-18" stroke="#fff" stroke-width="2"/>
        <line x1="-8" y1="-5" x2="12" y2="-10" stroke="#fff" stroke-width="2"/>
        <line x1="-5" y1="5" x2="15" y2="0" stroke="#fff" stroke-width="2"/>
        <line x1="-25" y1="20" x2="30" y2="20" stroke="#1a252f" stroke-width="1"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">shoes</text>
    </g>

    <!-- ============================================ -->
    <!--     TRANSPORT (TRANSPORTE)                  -->
    <!-- ============================================ -->

    <!-- CARD BUS -->
    <g v-if="type === 'card-bus'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#27ae60"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">A</text>
      <g transform="translate(60, 72)">
        <rect x="-35" y="-25" width="70" height="45" rx="8" fill="#f39c12"/>
        <rect x="-30" y="-20" width="18" height="15" rx="2" fill="#85c1e9"/>
        <rect x="-8" y="-20" width="18" height="15" rx="2" fill="#85c1e9"/>
        <rect x="14" y="-20" width="18" height="15" rx="2" fill="#85c1e9"/>
        <rect x="-35" y="0" width="70" height="8" fill="#d68910"/>
        <rect x="-35" y="-25" width="70" height="5" rx="3" fill="#2c3e50"/>
        <circle cx="-20" cy="22" r="8" fill="#2c3e50"/>
        <circle cx="-20" cy="22" r="4" fill="#7f8c8d"/>
        <circle cx="20" cy="22" r="8" fill="#2c3e50"/>
        <circle cx="20" cy="22" r="4" fill="#7f8c8d"/>
        <rect x="-33" y="10" width="6" height="4" rx="1" fill="#f5b041"/>
        <rect x="27" y="10" width="6" height="4" rx="1" fill="#e74c3c"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">bus</text>
    </g>

    <!-- CARD CAR -->
    <g v-if="type === 'card-car'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#27ae60"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">B</text>
      <g transform="translate(60, 75)">
        <rect x="-38" y="-5" width="76" height="22" rx="5" fill="#e74c3c"/>
        <path d="M-25,-5 L-20,-25 L20,-25 L28,-5 Z" fill="#e74c3c"/>
        <path d="M-22,-8 L-18,-22 L-2,-22 L-2,-8 Z" fill="#85c1e9"/>
        <path d="M2,-8 L2,-22 L18,-22 L24,-8 Z" fill="#85c1e9"/>
        <circle cx="-22" cy="18" r="10" fill="#2c3e50"/>
        <circle cx="-22" cy="18" r="5" fill="#7f8c8d"/>
        <circle cx="22" cy="18" r="10" fill="#2c3e50"/>
        <circle cx="22" cy="18" r="5" fill="#7f8c8d"/>
        <rect x="-38" y="0" width="8" height="6" rx="2" fill="#f5b041"/>
        <rect x="30" y="0" width="8" height="6" rx="2" fill="#c0392b"/>
        <rect x="5" y="-2" width="8" height="3" rx="1" fill="#c0392b"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">car</text>
    </g>

    <!-- CARD BICYCLE -->
    <g v-if="type === 'card-bicycle'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#27ae60"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">C</text>
      <g transform="translate(60, 75)">
        <circle cx="-22" cy="10" r="18" fill="none" stroke="#2c3e50" stroke-width="3"/>
        <circle cx="-22" cy="10" r="3" fill="#2c3e50"/>
        <circle cx="22" cy="10" r="18" fill="none" stroke="#2c3e50" stroke-width="3"/>
        <circle cx="22" cy="10" r="3" fill="#2c3e50"/>
        <line x1="-22" y1="10" x2="0" y2="-15" stroke="#3498db" stroke-width="4"/>
        <line x1="0" y1="-15" x2="22" y2="10" stroke="#3498db" stroke-width="4"/>
        <line x1="-22" y1="10" x2="0" y2="5" stroke="#3498db" stroke-width="4"/>
        <line x1="0" y1="5" x2="0" y2="-15" stroke="#3498db" stroke-width="4"/>
        <line x1="22" y1="10" x2="25" y2="-15" stroke="#2c3e50" stroke-width="3"/>
        <line x1="18" y1="-18" x2="32" y2="-18" stroke="#2c3e50" stroke-width="3"/>
        <ellipse cx="-5" cy="-20" rx="10" ry="4" fill="#2c3e50"/>
        <line x1="0" y1="-15" x2="-2" y2="-20" stroke="#2c3e50" stroke-width="3"/>
        <circle cx="0" cy="5" r="5" fill="#2c3e50"/>
        <line x1="-5" y1="8" x2="5" y2="2" stroke="#2c3e50" stroke-width="2"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">bicycle</text>
    </g>

    <!-- ============================================ -->
    <!--     OBJECTS (OBJETOS)                       -->
    <!-- ============================================ -->

    <!-- CARD BOOK -->
    <g v-if="type === 'card-book'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#9b59b6"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">A</text>
      <g transform="translate(60, 72)">
        <rect x="-30" y="-25" width="8" height="50" fill="#8e44ad"/>
        <rect x="-22" y="-25" width="50" height="50" rx="2" fill="#9b59b6"/>
        <rect x="-20" y="-22" width="45" height="44" fill="#fdfefe"/>
        <line x1="-18" y1="-15" x2="20" y2="-15" stroke="#e0e0e0" stroke-width="1"/>
        <line x1="-18" y1="-5" x2="20" y2="-5" stroke="#e0e0e0" stroke-width="1"/>
        <line x1="-18" y1="5" x2="20" y2="5" stroke="#e0e0e0" stroke-width="1"/>
        <line x1="-18" y1="15" x2="15" y2="15" stroke="#e0e0e0" stroke-width="1"/>
        <line x1="-26" y1="-20" x2="-26" y2="20" stroke="#7d3c98" stroke-width="2"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">book</text>
    </g>

    <!-- CARD PENCIL -->
    <g v-if="type === 'card-pencil'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#9b59b6"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">B</text>
      <g transform="translate(60, 72) rotate(-45)">
        <rect x="-8" y="-40" width="16" height="70" fill="#f1c40f"/>
        <rect x="-8" y="20" width="16" height="8" fill="#27ae60"/>
        <polygon points="-8,30 8,30 0,50" fill="#d4a574"/>
        <polygon points="-3,42 3,42 0,50" fill="#2c3e50"/>
        <rect x="-8" y="-45" width="16" height="8" rx="2" fill="#e91e63"/>
        <rect x="-8" y="-40" width="16" height="4" fill="#bdc3c7"/>
        <line x1="-4" y1="-35" x2="-4" y2="25" stroke="#d4a800" stroke-width="1"/>
        <line x1="4" y1="-35" x2="4" y2="25" stroke="#d4a800" stroke-width="1"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">pencil</text>
    </g>

    <!-- CARD CLOCK -->
    <g v-if="type === 'card-clock'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#9b59b6"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">C</text>
      <g transform="translate(60, 70)">
        <circle cx="0" cy="0" r="32" fill="#2c3e50"/>
        <circle cx="0" cy="0" r="28" fill="#ecf0f1"/>
        <line x1="0" y1="-24" x2="0" y2="-20" stroke="#2c3e50" stroke-width="2"/>
        <line x1="0" y1="24" x2="0" y2="20" stroke="#2c3e50" stroke-width="2"/>
        <line x1="-24" y1="0" x2="-20" y2="0" stroke="#2c3e50" stroke-width="2"/>
        <line x1="24" y1="0" x2="20" y2="0" stroke="#2c3e50" stroke-width="2"/>
        <line x1="0" y1="0" x2="0" y2="-12" stroke="#2c3e50" stroke-width="3" stroke-linecap="round"/>
        <line x1="0" y1="0" x2="10" y2="-10" stroke="#2c3e50" stroke-width="2" stroke-linecap="round"/>
        <circle cx="0" cy="0" r="3" fill="#e74c3c"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">clock</text>
    </g>

    <!-- ============================================ -->
    <!--     PLACES (LUGARES)                        -->
    <!-- ============================================ -->

    <!-- CARD HOUSE -->
    <g v-if="type === 'card-house'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#e67e22"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">A</text>
      <g transform="translate(60, 75)">
        <polygon points="0,-35 -40,0 40,0" fill="#c0392b"/>
        <rect x="-32" y="0" width="64" height="35" fill="#f5b041"/>
        <rect x="-8" y="10" width="16" height="25" fill="#8B4513"/>
        <circle cx="5" cy="22" r="2" fill="#d4a800"/>
        <rect x="-28" y="8" width="14" height="14" fill="#85c1e9"/>
        <line x1="-21" y1="8" x2="-21" y2="22" stroke="#fff" stroke-width="2"/>
        <line x1="-28" y1="15" x2="-14" y2="15" stroke="#fff" stroke-width="2"/>
        <rect x="14" y="8" width="14" height="14" fill="#85c1e9"/>
        <line x1="21" y1="8" x2="21" y2="22" stroke="#fff" stroke-width="2"/>
        <line x1="14" y1="15" x2="28" y2="15" stroke="#fff" stroke-width="2"/>
        <rect x="15" y="-25" width="12" height="20" fill="#7f8c8d"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">house</text>
    </g>

    <!-- CARD SCHOOL -->
    <g v-if="type === 'card-school'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#e67e22"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">B</text>
      <g transform="translate(60, 75)">
        <rect x="-35" y="-5" width="70" height="40" fill="#ecf0f1"/>
        <rect x="-12" y="-30" width="24" height="25" fill="#bdc3c7"/>
        <polygon points="0,-40 -15,-30 15,-30" fill="#e74c3c"/>
        <circle cx="0" cy="-18" r="8" fill="#fff" stroke="#2c3e50" stroke-width="1"/>
        <line x1="0" y1="-18" x2="0" y2="-22" stroke="#2c3e50" stroke-width="1"/>
        <line x1="0" y1="-18" x2="3" y2="-16" stroke="#2c3e50" stroke-width="1"/>
        <rect x="-8" y="10" width="16" height="25" fill="#8B4513"/>
        <rect x="-30" y="5" width="10" height="12" fill="#85c1e9"/>
        <rect x="20" y="5" width="10" height="12" fill="#85c1e9"/>
        <rect x="-30" y="20" width="10" height="12" fill="#85c1e9"/>
        <rect x="20" y="20" width="10" height="12" fill="#85c1e9"/>
        <line x1="0" y1="-40" x2="0" y2="-50" stroke="#2c3e50" stroke-width="2"/>
        <rect x="0" y="-50" width="12" height="8" fill="#e74c3c"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">school</text>
    </g>

    <!-- CARD HOSPITAL -->
    <g v-if="type === 'card-hospital'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#e67e22"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">C</text>
      <g transform="translate(60, 72)">
        <rect x="-32" y="-20" width="64" height="55" fill="#ecf0f1"/>
        <rect x="-8" y="-35" width="16" height="20" fill="#e74c3c"/>
        <rect x="-15" y="-28" width="30" height="6" fill="#e74c3c"/>
        <rect x="-10" y="15" width="20" height="20" fill="#3498db"/>
        <line x1="0" y1="15" x2="0" y2="35" stroke="#2980b9" stroke-width="2"/>
        <rect x="-28" y="-12" width="12" height="10" fill="#85c1e9"/>
        <rect x="16" y="-12" width="12" height="10" fill="#85c1e9"/>
        <rect x="-28" y="5" width="12" height="10" fill="#85c1e9"/>
        <rect x="16" y="5" width="12" height="10" fill="#85c1e9"/>
        <circle cx="0" cy="-25" r="12" fill="#fff"/>
        <text x="0" y="-20" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#e74c3c">H</text>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">hospital</text>
    </g>

    <!-- ============================================ -->
    <!--     ANIMALS (ANIMALES)                      -->
    <!-- ============================================ -->

    <!-- CARD DOG -->
    <g v-if="type === 'card-dog'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#1abc9c"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">A</text>
      <g transform="translate(60, 72)">
        <ellipse cx="0" cy="10" rx="28" ry="20" fill="#d4a574"/>
        <circle cx="-20" cy="-10" r="18" fill="#d4a574"/>
        <ellipse cx="-32" cy="-22" rx="8" ry="14" fill="#b5865a" transform="rotate(-20 -32 -22)"/>
        <ellipse cx="-8" cy="-25" rx="8" ry="14" fill="#b5865a" transform="rotate(20 -8 -25)"/>
        <ellipse cx="-28" cy="-5" rx="10" ry="8" fill="#f5d5c0"/>
        <ellipse cx="-32" cy="-6" rx="5" ry="4" fill="#2c3e50"/>
        <circle cx="-25" cy="-15" r="4" fill="#2c3e50"/>
        <circle cx="-12" cy="-15" r="4" fill="#2c3e50"/>
        <circle cx="-24" cy="-16" r="1.5" fill="#fff"/>
        <circle cx="-11" cy="-16" r="1.5" fill="#fff"/>
        <ellipse cx="-18" cy="30" rx="6" ry="5" fill="#d4a574"/>
        <ellipse cx="0" cy="30" rx="6" ry="5" fill="#d4a574"/>
        <ellipse cx="18" cy="30" rx="6" ry="5" fill="#d4a574"/>
        <path d="M28,5 Q45,-10 40,-25" fill="none" stroke="#d4a574" stroke-width="8" stroke-linecap="round"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">dog</text>
    </g>

    <!-- CARD CAT -->
    <g v-if="type === 'card-cat'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#1abc9c"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">B</text>
      <g transform="translate(60, 72)">
        <ellipse cx="5" cy="10" rx="25" ry="18" fill="#7f8c8d"/>
        <circle cx="-15" cy="-5" r="20" fill="#95a5a6"/>
        <polygon points="-30,-20 -25,-40 -15,-22" fill="#95a5a6"/>
        <polygon points="0,-20 -5,-40 -15,-22" fill="#95a5a6"/>
        <polygon points="-28,-22 -25,-35 -18,-24" fill="#ffb6c1"/>
        <polygon points="-2,-22 -5,-35 -12,-24" fill="#ffb6c1"/>
        <ellipse cx="-22" cy="-8" rx="5" ry="6" fill="#2ecc71"/>
        <ellipse cx="-8" cy="-8" rx="5" ry="6" fill="#2ecc71"/>
        <ellipse cx="-22" cy="-8" rx="2" ry="5" fill="#2c3e50"/>
        <ellipse cx="-8" cy="-8" rx="2" ry="5" fill="#2c3e50"/>
        <polygon points="-15,0 -18,5 -12,5" fill="#ffb6c1"/>
        <line x1="-35" y1="0" x2="-25" y2="2" stroke="#2c3e50" stroke-width="1"/>
        <line x1="-35" y1="5" x2="-25" y2="5" stroke="#2c3e50" stroke-width="1"/>
        <line x1="5" y1="0" x2="-5" y2="2" stroke="#2c3e50" stroke-width="1"/>
        <line x1="5" y1="5" x2="-5" y2="5" stroke="#2c3e50" stroke-width="1"/>
        <ellipse cx="-10" cy="28" rx="5" ry="4" fill="#95a5a6"/>
        <ellipse cx="5" cy="28" rx="5" ry="4" fill="#95a5a6"/>
        <ellipse cx="20" cy="28" rx="5" ry="4" fill="#95a5a6"/>
        <path d="M30,10 Q50,0 45,-20" fill="none" stroke="#7f8c8d" stroke-width="8" stroke-linecap="round"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">cat</text>
    </g>

    <!-- CARD BIRD -->
    <g v-if="type === 'card-bird'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#1abc9c"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">C</text>
      <g transform="translate(60, 70)">
        <ellipse cx="0" cy="5" rx="22" ry="18" fill="#3498db"/>
        <circle cx="-18" cy="-12" r="14" fill="#3498db"/>
        <circle cx="-22" cy="-14" r="4" fill="#fff"/>
        <circle cx="-23" cy="-14" r="2" fill="#2c3e50"/>
        <polygon points="-32,-12 -45,-10 -32,-6" fill="#f39c12"/>
        <ellipse cx="5" cy="0" rx="18" ry="12" fill="#2980b9"/>
        <polygon points="22,0 40,-8 38,5 40,15 22,10" fill="#2980b9"/>
        <line x1="-8" y1="22" x2="-12" y2="35" stroke="#f39c12" stroke-width="2"/>
        <line x1="-12" y1="35" x2="-18" y2="35" stroke="#f39c12" stroke-width="2"/>
        <line x1="-12" y1="35" x2="-10" y2="38" stroke="#f39c12" stroke-width="2"/>
        <line x1="5" y1="22" x2="2" y2="35" stroke="#f39c12" stroke-width="2"/>
        <line x1="2" y1="35" x2="-4" y2="35" stroke="#f39c12" stroke-width="2"/>
        <line x1="2" y1="35" x2="4" y2="38" stroke="#f39c12" stroke-width="2"/>
        <ellipse cx="-10" cy="10" rx="10" ry="8" fill="#85c1e9"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">bird</text>
    </g>

    <!-- ============================================ -->
    <!--     WEATHER (CLIMA)                         -->
    <!-- ============================================ -->

    <!-- CARD SUN -->
    <g v-if="type === 'card-sun'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#f39c12"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">A</text>
      <g transform="translate(60, 70)">
        <line x1="0" y1="-40" x2="0" y2="-28" stroke="#f39c12" stroke-width="4" stroke-linecap="round"/>
        <line x1="0" y1="28" x2="0" y2="40" stroke="#f39c12" stroke-width="4" stroke-linecap="round"/>
        <line x1="-40" y1="0" x2="-28" y2="0" stroke="#f39c12" stroke-width="4" stroke-linecap="round"/>
        <line x1="28" y1="0" x2="40" y2="0" stroke="#f39c12" stroke-width="4" stroke-linecap="round"/>
        <line x1="-28" y1="-28" x2="-20" y2="-20" stroke="#f39c12" stroke-width="4" stroke-linecap="round"/>
        <line x1="28" y1="-28" x2="20" y2="-20" stroke="#f39c12" stroke-width="4" stroke-linecap="round"/>
        <line x1="-28" y1="28" x2="-20" y2="20" stroke="#f39c12" stroke-width="4" stroke-linecap="round"/>
        <line x1="28" y1="28" x2="20" y2="20" stroke="#f39c12" stroke-width="4" stroke-linecap="round"/>
        <circle cx="0" cy="0" r="22" fill="#f1c40f"/>
        <circle cx="-8" cy="-5" r="3" fill="#e67e22"/>
        <circle cx="8" cy="-5" r="3" fill="#e67e22"/>
        <path d="M-10,8 Q0,16 10,8" fill="none" stroke="#e67e22" stroke-width="3" stroke-linecap="round"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">sun</text>
    </g>

    <!-- CARD RAIN -->
    <g v-if="type === 'card-rain'">
      <rect x="5" y="5" width="110" height="140" rx="10" fill="#ffffff" stroke="#e0e0e0" stroke-width="2"/>
      <circle cx="25" cy="25" r="14" fill="#f39c12"/>
      <text x="25" y="30" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#ffffff">B</text>
      <g transform="translate(60, 60)">
        <ellipse cx="-15" cy="0" rx="20" ry="15" fill="#95a5a6"/>
        <ellipse cx="10" cy="-5" rx="22" ry="18" fill="#bdc3c7"/>
        <ellipse cx="0" cy="5" rx="25" ry="12" fill="#95a5a6"/>
        <ellipse cx="25" cy="0" rx="15" ry="12" fill="#bdc3c7"/>
        <path d="M-20,25 Q-22,32 -20,35 Q-18,38 -16,35 Q-14,32 -16,25 Z" fill="#3498db"/>
        <path d="M-5,30 Q-7,37 -5,40 Q-3,43 -1,40 Q1,37 -1,30 Z" fill="#3498db"/>
        <path d="M10,25 Q8,32 10,35 Q12,38 14,35 Q16,32 14,25 Z" fill="#3498db"/>
        <path d="M25,32 Q23,39 25,42 Q27,45 29,42 Q31,39 29,32 Z" fill="#3498db"/>
        <path d="M-12,40 Q-14,47 -12,50 Q-10,53 -8,50 Q-6,47 -8,40 Z" fill="#3498db"/>
        <path d="M18,38 Q16,45 18,48 Q20,51 22,48 Q24,45 22,38 Z" fill="#3498db"/>
      </g>
      <text x="60" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#333">rain</text>
    </g>

    <text
      v-if="label"
      x="60"
      y="145"
      font-family="sans-serif"
      font-size="12"
      fill="#666"
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
  width: { type: Number, default: 120 }, // Ancho base de la tarjeta
  type: { type: String, default: 'card-apple' },
  label: { type: String, default: '' }
});

// Calculamos escala basada en el ancho deseado
const scale = computed(() => {
  return props.width / 120;
});
</script>
