<template>
  <g :transform="`translate(${x}, ${y}) scale(${scale})`">
    
    <!-- ============================================ -->
    <!--     ATM (CAJEROS AUTOMÁTICOS)               -->
    <!-- ============================================ -->

    <!-- ATM: INSERT CARD -->
    <g v-if="type === 'atm-insert-card'">
      <rect x="10" y="10" width="300" height="200" rx="12" fill="#2c3e50" stroke="#1a252f" stroke-width="4"/>
      <rect x="25" y="25" width="270" height="130" rx="6" fill="#1a1a2e"/>
      <g transform="translate(160, 70)">
        <rect x="-40" y="-25" width="80" height="50" rx="5" fill="#f1c40f" stroke="#d4a800" stroke-width="2"/>
        <rect x="-35" y="-15" width="25" height="18" rx="2" fill="#d4a800"/>
        <line x1="-35" y1="15" x2="35" y2="15" stroke="#d4a800" stroke-width="3"/>
      </g>
      <g transform="translate(160, 125)">
        <line x1="-20" y1="0" x2="20" y2="0" stroke="#3498db" stroke-width="3"/>
        <polygon points="20,-8 35,0 20,8" fill="#3498db"/>
      </g>
      <text x="160" y="155" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#3498db">INSERT CARD</text>
      <rect x="120" y="170" width="80" height="8" rx="2" fill="#1a252f"/>
      <rect x="125" y="172" width="70" height="4" rx="1" fill="#0d1318"/>
      <circle cx="220" cy="185" r="5" fill="#27ae60">
        <animate attributeName="opacity" values="1;0.3;1" dur="1.5s" repeatCount="indefinite"/>
      </circle>
    </g>

    <!-- ATM: ENTER PIN -->
    <g v-if="type === 'atm-enter-pin'">
      <rect x="10" y="10" width="300" height="200" rx="12" fill="#2c3e50" stroke="#1a252f" stroke-width="4"/>
      <rect x="25" y="25" width="270" height="130" rx="6" fill="#1a1a2e"/>
      <text x="160" y="55" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#3498db">ENTER YOUR PIN</text>
      <rect x="80" y="70" width="160" height="35" rx="4" fill="#0d1318" stroke="#3498db" stroke-width="2"/>
      <text x="160" y="95" text-anchor="middle" font-family="monospace" font-size="24" fill="#3498db">* * * *</text>
      <g transform="translate(85, 115)">
        <rect x="0" y="0" width="30" height="20" rx="3" fill="#34495e"/>
        <text x="15" y="15" text-anchor="middle" font-family="Arial" font-size="12" fill="#fff">1</text>
        <rect x="35" y="0" width="30" height="20" rx="3" fill="#34495e"/>
        <text x="50" y="15" text-anchor="middle" font-family="Arial" font-size="12" fill="#fff">2</text>
        <rect x="70" y="0" width="30" height="20" rx="3" fill="#34495e"/>
        <text x="85" y="15" text-anchor="middle" font-family="Arial" font-size="12" fill="#fff">3</text>
        <rect x="105" y="0" width="45" height="20" rx="3" fill="#27ae60"/>
        <text x="127" y="15" text-anchor="middle" font-family="Arial" font-size="10" fill="#fff">OK</text>
      </g>
      <text x="160" y="150" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" fill="#7f8c8d">Press OK when finished</text>
      <rect x="120" y="170" width="80" height="8" rx="2" fill="#1a252f"/>
      <circle cx="220" cy="185" r="5" fill="#f39c12"/>
    </g>

    <!-- ATM: SELECT AMOUNT -->
    <g v-if="type === 'atm-select-amount'">
      <rect x="10" y="10" width="300" height="200" rx="12" fill="#2c3e50" stroke="#1a252f" stroke-width="4"/>
      <rect x="25" y="25" width="270" height="130" rx="6" fill="#1a1a2e"/>
      <text x="160" y="50" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#3498db">SELECT AMOUNT</text>
      <g transform="translate(45, 60)">
        <rect x="0" y="0" width="90" height="28" rx="4" fill="#34495e"/>
        <text x="45" y="19" text-anchor="middle" font-family="Arial" font-size="12" fill="#fff">$20</text>
        <rect x="0" y="35" width="90" height="28" rx="4" fill="#34495e"/>
        <text x="45" y="54" text-anchor="middle" font-family="Arial" font-size="12" fill="#fff">$50</text>
        <rect x="0" y="70" width="90" height="28" rx="4" fill="#34495e"/>
        <text x="45" y="89" text-anchor="middle" font-family="Arial" font-size="12" fill="#fff">$100</text>
      </g>
      <g transform="translate(185, 60)">
        <rect x="0" y="0" width="90" height="28" rx="4" fill="#34495e"/>
        <text x="45" y="19" text-anchor="middle" font-family="Arial" font-size="12" fill="#fff">$200</text>
        <rect x="0" y="35" width="90" height="28" rx="4" fill="#34495e"/>
        <text x="45" y="54" text-anchor="middle" font-family="Arial" font-size="12" fill="#fff">$500</text>
        <rect x="0" y="70" width="90" height="28" rx="4" fill="#27ae60"/>
        <text x="45" y="89" text-anchor="middle" font-family="Arial" font-size="11" fill="#fff">OTHER</text>
      </g>
      <rect x="250" y="165" width="50" height="35" rx="3" fill="#1a252f" stroke="#27ae60" stroke-width="2"/>
      <text x="275" y="186" text-anchor="middle" font-family="Arial" font-size="8" fill="#27ae60">CASH</text>
    </g>

    <!-- ATM: OUT OF SERVICE -->
    <g v-if="type === 'atm-out-of-service'">
      <rect x="10" y="10" width="300" height="200" rx="12" fill="#2c3e50" stroke="#1a252f" stroke-width="4"/>
      <rect x="25" y="25" width="270" height="130" rx="6" fill="#1a1a2e"/>
      <g transform="translate(160, 75)">
        <circle cx="0" cy="0" r="35" fill="none" stroke="#e74c3c" stroke-width="4"/>
        <line x1="-18" y1="-18" x2="18" y2="18" stroke="#e74c3c" stroke-width="5" stroke-linecap="round"/>
        <line x1="18" y1="-18" x2="-18" y2="18" stroke="#e74c3c" stroke-width="5" stroke-linecap="round"/>
      </g>
      <text x="160" y="130" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#e74c3c">OUT OF SERVICE</text>
      <text x="160" y="148" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" fill="#7f8c8d">We apologize for the inconvenience</text>
      <rect x="120" y="170" width="80" height="8" rx="2" fill="#1a252f"/>
      <line x1="120" y1="174" x2="200" y2="174" stroke="#c0392b" stroke-width="2"/>
      <circle cx="220" cy="185" r="5" fill="#e74c3c"/>
    </g>

    <!-- ============================================ -->
    <!--     VENDING MACHINES                        -->
    <!-- ============================================ -->

    <!-- VENDING: SELECT PRODUCT -->
    <g v-if="type === 'vending-select-product'">
      <rect x="10" y="10" width="280" height="230" rx="8" fill="#34495e" stroke="#2c3e50" stroke-width="4"/>
      <rect x="25" y="20" width="150" height="50" rx="4" fill="#0d1318"/>
      <text x="100" y="40" text-anchor="middle" font-family="monospace" font-size="11" fill="#27ae60">SELECT ITEM</text>
      <text x="100" y="58" text-anchor="middle" font-family="monospace" font-size="18" fill="#27ae60">A - 5</text>
      <g transform="translate(190, 20)">
        <rect x="0" y="0" width="85" height="50" rx="4" fill="#2c3e50"/>
        <g transform="translate(5, 5)">
          <rect x="0" y="0" width="22" height="18" rx="2" fill="#7f8c8d"/>
          <text x="11" y="13" text-anchor="middle" font-family="Arial" font-size="10" fill="#fff">1</text>
          <rect x="26" y="0" width="22" height="18" rx="2" fill="#7f8c8d"/>
          <text x="37" y="13" text-anchor="middle" font-family="Arial" font-size="10" fill="#fff">2</text>
          <rect x="52" y="0" width="22" height="18" rx="2" fill="#7f8c8d"/>
          <text x="63" y="13" text-anchor="middle" font-family="Arial" font-size="10" fill="#fff">3</text>
          <rect x="0" y="22" width="22" height="18" rx="2" fill="#7f8c8d"/>
          <text x="11" y="35" text-anchor="middle" font-family="Arial" font-size="10" fill="#fff">4</text>
          <rect x="26" y="22" width="22" height="18" rx="2" fill="#7f8c8d"/>
          <text x="37" y="35" text-anchor="middle" font-family="Arial" font-size="10" fill="#fff">5</text>
          <rect x="52" y="22" width="22" height="18" rx="2" fill="#27ae60"/>
          <text x="63" y="35" text-anchor="middle" font-family="Arial" font-size="8" fill="#fff">OK</text>
        </g>
      </g>
      <rect x="25" y="80" width="250" height="110" rx="4" fill="#ecf0f1"/>
      <g transform="translate(35, 90)">
        <rect x="0" y="0" width="50" height="45" rx="3" fill="#e74c3c" opacity="0.8"/>
        <text x="25" y="55" text-anchor="middle" font-family="Arial" font-size="9" fill="#333">A1</text>
        <rect x="60" y="0" width="50" height="45" rx="3" fill="#3498db" opacity="0.8"/>
        <text x="85" y="55" text-anchor="middle" font-family="Arial" font-size="9" fill="#333">A2</text>
        <rect x="120" y="0" width="50" height="45" rx="3" fill="#27ae60" opacity="0.8"/>
        <text x="145" y="55" text-anchor="middle" font-family="Arial" font-size="9" fill="#333">A3</text>
        <rect x="180" y="0" width="50" height="45" rx="3" fill="#f39c12" opacity="0.8"/>
        <text x="205" y="55" text-anchor="middle" font-family="Arial" font-size="9" fill="#333">A4</text>
      </g>
      <g transform="translate(35, 145)">
        <rect x="0" y="0" width="50" height="35" rx="3" fill="#9b59b6" opacity="0.8"/>
        <text x="25" y="42" text-anchor="middle" font-family="Arial" font-size="9" fill="#333">B1</text>
        <rect x="60" y="0" width="50" height="35" rx="3" fill="#1abc9c" opacity="0.8"/>
        <text x="85" y="42" text-anchor="middle" font-family="Arial" font-size="9" fill="#333">B2</text>
        <rect x="120" y="0" width="50" height="35" rx="3" fill="#e67e22" opacity="0.8"/>
        <text x="145" y="42" text-anchor="middle" font-family="Arial" font-size="9" fill="#333">B3</text>
        <rect x="180" y="0" width="50" height="35" rx="3" fill="#34495e" opacity="0.8"/>
        <text x="205" y="42" text-anchor="middle" font-family="Arial" font-size="9" fill="#333">B4</text>
      </g>
      <rect x="80" y="200" width="140" height="30" rx="4" fill="#1a252f"/>
      <text x="150" y="220" text-anchor="middle" font-family="Arial" font-size="10" fill="#7f8c8d">COLLECT ITEM</text>
    </g>

    <!-- VENDING: INSERT COIN -->
    <g v-if="type === 'vending-insert-coin'">
      <rect x="10" y="10" width="280" height="180" rx="8" fill="#34495e" stroke="#2c3e50" stroke-width="4"/>
      <rect x="25" y="20" width="250" height="60" rx="4" fill="#0d1318"/>
      <text x="150" y="45" text-anchor="middle" font-family="monospace" font-size="12" fill="#f39c12">PRICE:</text>
      <text x="150" y="68" text-anchor="middle" font-family="monospace" font-size="22" fill="#27ae60">$1.50</text>
      <g transform="translate(80, 120)">
        <circle cx="0" cy="0" r="25" fill="#f1c40f" stroke="#d4a800" stroke-width="3"/>
        <text x="0" y="6" text-anchor="middle" font-family="Arial" font-size="14" fill="#d4a800">$</text>
        <line x1="35" y1="0" x2="65" y2="0" stroke="#3498db" stroke-width="3"/>
        <polygon points="65,-7 80,0 65,7" fill="#3498db"/>
      </g>
      <g transform="translate(180, 100)">
        <rect x="0" y="0" width="60" height="45" rx="4" fill="#2c3e50"/>
        <ellipse cx="30" cy="22" rx="12" ry="18" fill="#1a252f"/>
        <text x="30" y="50" text-anchor="middle" font-family="Arial" font-size="8" fill="#7f8c8d">COINS</text>
      </g>
      <text x="150" y="170" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" fill="#3498db">INSERT COIN TO CONTINUE</text>
    </g>

    <!-- VENDING: SOLD OUT -->
    <g v-if="type === 'vending-sold-out'">
      <rect x="10" y="10" width="280" height="160" rx="8" fill="#34495e" stroke="#2c3e50" stroke-width="4"/>
      <rect x="25" y="20" width="250" height="100" rx="4" fill="#0d1318"/>
      <g transform="translate(150, 60)">
        <rect x="-30" y="-25" width="60" height="50" rx="5" fill="#7f8c8d" opacity="0.5"/>
        <line x1="-35" y1="-30" x2="35" y2="30" stroke="#e74c3c" stroke-width="5" stroke-linecap="round"/>
        <line x1="35" y1="-30" x2="-35" y2="30" stroke="#e74c3c" stroke-width="5" stroke-linecap="round"/>
      </g>
      <text x="150" y="105" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#e74c3c">SOLD OUT</text>
      <text x="150" y="145" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" fill="#7f8c8d">Please select another item</text>
      <circle cx="260" cy="145" r="6" fill="#e74c3c">
        <animate attributeName="opacity" values="1;0.3;1" dur="1s" repeatCount="indefinite"/>
      </circle>
    </g>

    <!-- ============================================ -->
    <!--     AIRPORT (AEROPUERTO)                    -->
    <!-- ============================================ -->

    <!-- AIRPORT: GATE INFO -->
    <g v-if="type === 'airport-gate-info'">
      <rect x="10" y="10" width="380" height="180" rx="6" fill="#1a1a2e" stroke="#2c3e50" stroke-width="4"/>
      <rect x="15" y="15" width="370" height="35" fill="#2c3e50"/>
      <text x="200" y="40" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="#ffffff">DEPARTURE INFORMATION</text>
      <g transform="translate(0, 58)">
        <text x="40" y="12" font-family="Arial" font-size="10" fill="#3498db">FLIGHT</text>
        <text x="120" y="12" font-family="Arial" font-size="10" fill="#3498db">DESTINATION</text>
        <text x="250" y="12" font-family="Arial" font-size="10" fill="#3498db">TIME</text>
        <text x="320" y="12" font-family="Arial" font-size="10" fill="#3498db">GATE</text>
        <text x="365" y="12" font-family="Arial" font-size="10" fill="#3498db">STATUS</text>
      </g>
      <line x1="20" y1="75" x2="380" y2="75" stroke="#34495e" stroke-width="1"/>
      <g transform="translate(0, 85)">
        <text x="40" y="12" font-family="monospace" font-size="12" fill="#ffffff">AA 234</text>
        <text x="120" y="12" font-family="Arial" font-size="12" fill="#ffffff">NEW YORK</text>
        <text x="250" y="12" font-family="monospace" font-size="12" fill="#ffffff">14:30</text>
        <text x="320" y="12" font-family="monospace" font-size="14" fill="#f1c40f">B12</text>
        <text x="365" y="12" font-family="Arial" font-size="10" fill="#27ae60">ON TIME</text>
      </g>
      <g transform="translate(0, 110)">
        <text x="40" y="12" font-family="monospace" font-size="12" fill="#ffffff">BA 456</text>
        <text x="120" y="12" font-family="Arial" font-size="12" fill="#ffffff">LONDON</text>
        <text x="250" y="12" font-family="monospace" font-size="12" fill="#ffffff">15:45</text>
        <text x="320" y="12" font-family="monospace" font-size="14" fill="#f1c40f">C08</text>
        <text x="365" y="12" font-family="Arial" font-size="10" fill="#f39c12">BOARDING</text>
      </g>
      <g transform="translate(0, 135)">
        <text x="40" y="12" font-family="monospace" font-size="12" fill="#ffffff">LH 789</text>
        <text x="120" y="12" font-family="Arial" font-size="12" fill="#ffffff">FRANKFURT</text>
        <text x="250" y="12" font-family="monospace" font-size="12" fill="#ffffff">16:20</text>
        <text x="320" y="12" font-family="monospace" font-size="14" fill="#f1c40f">A03</text>
        <text x="365" y="12" font-family="Arial" font-size="10" fill="#e74c3c">DELAYED</text>
      </g>
      <g transform="translate(0, 160)">
        <text x="40" y="12" font-family="monospace" font-size="12" fill="#ffffff">IB 321</text>
        <text x="120" y="12" font-family="Arial" font-size="12" fill="#ffffff">MADRID</text>
        <text x="250" y="12" font-family="monospace" font-size="12" fill="#ffffff">17:00</text>
        <text x="320" y="12" font-family="monospace" font-size="14" fill="#f1c40f">D15</text>
        <text x="365" y="12" font-family="Arial" font-size="10" fill="#27ae60">ON TIME</text>
      </g>
    </g>

    <!-- AIRPORT: BOARDING -->
    <g v-if="type === 'airport-boarding'">
      <rect x="10" y="10" width="330" height="180" rx="6" fill="#1a1a2e" stroke="#f39c12" stroke-width="4"/>
      <rect x="15" y="15" width="320" height="40" fill="#f39c12"/>
      <text x="175" y="42" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#1a1a2e">NOW BOARDING</text>
      <text x="175" y="80" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#3498db">FLIGHT</text>
      <text x="175" y="105" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#ffffff">AA 1234</text>
      <text x="175" y="130" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" fill="#ffffff">to NEW YORK (JFK)</text>
      <g transform="translate(175, 165)">
        <text x="0" y="0" text-anchor="middle" font-family="Arial" font-size="12" fill="#7f8c8d">GATE</text>
        <text x="0" y="22" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#f1c40f">B 12</text>
      </g>
      <circle cx="30" cy="35" r="8" fill="#1a1a2e">
        <animate attributeName="opacity" values="1;0;1" dur="0.8s" repeatCount="indefinite"/>
      </circle>
      <circle cx="320" cy="35" r="8" fill="#1a1a2e">
        <animate attributeName="opacity" values="1;0;1" dur="0.8s" repeatCount="indefinite"/>
      </circle>
    </g>

    <!-- AIRPORT: GATE CLOSED -->
    <g v-if="type === 'airport-gate-closed'">
      <rect x="10" y="10" width="330" height="160" rx="6" fill="#1a1a2e" stroke="#e74c3c" stroke-width="4"/>
      <rect x="15" y="15" width="320" height="40" fill="#c0392b"/>
      <text x="175" y="42" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#ffffff">GATE CLOSED</text>
      <g transform="translate(175, 95)">
        <rect x="-30" y="-25" width="60" height="50" rx="4" fill="none" stroke="#7f8c8d" stroke-width="3"/>
        <circle cx="20" cy="0" r="5" fill="#e74c3c"/>
        <line x1="-25" y1="-20" x2="25" y2="20" stroke="#e74c3c" stroke-width="4" stroke-linecap="round"/>
      </g>
      <text x="175" y="145" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#7f8c8d">Please contact airline staff</text>
      <text x="175" y="162" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" fill="#e74c3c">Flight AA 1234</text>
    </g>

    <!-- ============================================ -->
    <!--     PARKING (ESTACIONAMIENTO)               -->
    <!-- ============================================ -->

    <!-- PARKING: AVAILABLE -->
    <g v-if="type === 'parking-available'">
      <rect x="10" y="10" width="260" height="160" rx="8" fill="#2c3e50" stroke="#1a252f" stroke-width="4"/>
      <rect x="20" y="20" width="240" height="140" rx="4" fill="#0d1318"/>
      <g transform="translate(70, 70)">
        <rect x="-30" y="-30" width="60" height="60" rx="8" fill="#3498db"/>
        <text x="0" y="15" text-anchor="middle" font-family="Arial" font-size="45" font-weight="bold" fill="#ffffff">P</text>
      </g>
      <g transform="translate(180, 70)">
        <text x="0" y="-15" text-anchor="middle" font-family="Arial" font-size="12" fill="#7f8c8d">SPACES</text>
        <text x="0" y="20" text-anchor="middle" font-family="monospace" font-size="42" font-weight="bold" fill="#27ae60">156</text>
        <text x="0" y="40" text-anchor="middle" font-family="Arial" font-size="11" fill="#27ae60">AVAILABLE</text>
      </g>
      <g transform="translate(140, 135)">
        <text x="0" y="0" text-anchor="middle" font-family="Arial" font-size="10" fill="#7f8c8d">LEVEL 2 - SECTION B</text>
      </g>
    </g>

    <!-- PARKING: FULL -->
    <g v-if="type === 'parking-full'">
      <rect x="10" y="10" width="260" height="160" rx="8" fill="#2c3e50" stroke="#1a252f" stroke-width="4"/>
      <rect x="20" y="20" width="240" height="140" rx="4" fill="#0d1318"/>
      <g transform="translate(140, 70)">
        <rect x="-35" y="-35" width="70" height="70" rx="8" fill="#3498db"/>
        <text x="0" y="18" text-anchor="middle" font-family="Arial" font-size="50" font-weight="bold" fill="#ffffff">P</text>
        <circle cx="0" cy="0" r="40" fill="none" stroke="#e74c3c" stroke-width="6"/>
        <line x1="-28" y1="-28" x2="28" y2="28" stroke="#e74c3c" stroke-width="6" stroke-linecap="round"/>
      </g>
      <text x="140" y="130" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" font-weight="bold" fill="#e74c3c">FULL</text>
      <text x="140" y="150" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" fill="#7f8c8d">Try Level 3 or wait</text>
    </g>

    <!-- ============================================ -->
    <!--     OTHERS (OTROS)                          -->
    <!-- ============================================ -->

    <!-- TICKET MACHINE -->
    <g v-if="type === 'ticket-machine'">
      <rect x="10" y="10" width="280" height="200" rx="10" fill="#34495e" stroke="#2c3e50" stroke-width="4"/>
      <rect x="25" y="20" width="250" height="90" rx="4" fill="#0d1318"/>
      <text x="150" y="45" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#3498db">SELECT TICKET TYPE</text>
      <g transform="translate(35, 55)">
        <rect x="0" y="0" width="105" height="45" rx="4" fill="#27ae60"/>
        <text x="52" y="18" text-anchor="middle" font-family="Arial" font-size="11" fill="#fff">SINGLE</text>
        <text x="52" y="35" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#fff">$2.50</text>
      </g>
      <g transform="translate(155, 55)">
        <rect x="0" y="0" width="105" height="45" rx="4" fill="#3498db"/>
        <text x="52" y="18" text-anchor="middle" font-family="Arial" font-size="11" fill="#fff">RETURN</text>
        <text x="52" y="35" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#fff">$4.00</text>
      </g>
      <rect x="25" y="120" width="250" height="75" rx="4" fill="#2c3e50"/>
      <g transform="translate(50, 135)">
        <rect x="0" y="0" width="80" height="45" rx="4" fill="#1a252f"/>
        <rect x="15" y="15" width="50" height="6" rx="2" fill="#0d1318"/>
        <text x="40" y="40" text-anchor="middle" font-family="Arial" font-size="8" fill="#7f8c8d">INSERT CARD</text>
      </g>
      <g transform="translate(150, 135)">
        <rect x="0" y="0" width="50" height="45" rx="4" fill="#1a252f"/>
        <ellipse cx="25" cy="20" rx="10" ry="15" fill="#0d1318"/>
        <text x="25" y="40" text-anchor="middle" font-family="Arial" font-size="8" fill="#7f8c8d">COINS</text>
      </g>
      <g transform="translate(215, 135)">
        <rect x="0" y="0" width="50" height="45" rx="4" fill="#1a252f"/>
        <g transform="translate(25, 18)">
          <path d="M-8 5 Q0 -5 8 5" fill="none" stroke="#3498db" stroke-width="2"/>
          <path d="M-12 8 Q0 -8 12 8" fill="none" stroke="#3498db" stroke-width="2"/>
          <path d="M-16 11 Q0 -11 16 11" fill="none" stroke="#3498db" stroke-width="2"/>
        </g>
        <text x="25" y="40" text-anchor="middle" font-family="Arial" font-size="7" fill="#7f8c8d">TAP HERE</text>
      </g>
    </g>

    <!-- DIGITAL MENU BOARD -->
    <g v-if="type === 'digital-menu-board'">
      <rect x="10" y="10" width="330" height="230" rx="6" fill="#1a1a2e" stroke="#d35400" stroke-width="4"/>
      <rect x="15" y="15" width="320" height="40" fill="#e67e22"/>
      <text x="175" y="42" text-anchor="middle" font-family="Georgia, serif" font-size="22" font-weight="bold" fill="#ffffff">TODAY'S MENU</text>
      <g transform="translate(25, 65)">
        <text x="0" y="15" font-family="Arial" font-size="12" font-weight="bold" fill="#e67e22">MAIN DISHES</text>
        <text x="0" y="38" font-family="Arial" font-size="11" fill="#ffffff">Grilled Salmon</text>
        <text x="130" y="38" font-family="Arial" font-size="11" fill="#27ae60">$18.50</text>
        <text x="0" y="58" font-family="Arial" font-size="11" fill="#ffffff">Beef Steak</text>
        <text x="130" y="58" font-family="Arial" font-size="11" fill="#27ae60">$22.00</text>
        <text x="0" y="78" font-family="Arial" font-size="11" fill="#ffffff">Pasta Carbonara</text>
        <text x="130" y="78" font-family="Arial" font-size="11" fill="#27ae60">$14.00</text>
        <text x="0" y="98" font-family="Arial" font-size="11" fill="#ffffff">Caesar Salad</text>
        <text x="130" y="98" font-family="Arial" font-size="11" fill="#27ae60">$12.50</text>
      </g>
      <line x1="175" y1="70" x2="175" y2="220" stroke="#34495e" stroke-width="1"/>
      <g transform="translate(190, 65)">
        <text x="0" y="15" font-family="Arial" font-size="12" font-weight="bold" fill="#e67e22">DRINKS</text>
        <text x="0" y="38" font-family="Arial" font-size="11" fill="#ffffff">Coffee</text>
        <text x="115" y="38" font-family="Arial" font-size="11" fill="#27ae60">$3.50</text>
        <text x="0" y="58" font-family="Arial" font-size="11" fill="#ffffff">Fresh Juice</text>
        <text x="115" y="58" font-family="Arial" font-size="11" fill="#27ae60">$4.50</text>
        <text x="0" y="78" font-family="Arial" font-size="11" fill="#ffffff">Soft Drinks</text>
        <text x="115" y="78" font-family="Arial" font-size="11" fill="#27ae60">$2.50</text>
        <text x="0" y="98" font-family="Arial" font-size="11" fill="#ffffff">Mineral Water</text>
        <text x="115" y="98" font-family="Arial" font-size="11" fill="#27ae60">$2.00</text>
      </g>
      <rect x="25" y="175" width="300" height="50" rx="4" fill="#c0392b"/>
      <text x="175" y="195" text-anchor="middle" font-family="Arial" font-size="11" fill="#f1c40f">⭐ TODAY'S SPECIAL ⭐</text>
      <text x="175" y="215" text-anchor="middle" font-family="Arial" font-size="13" font-weight="bold" fill="#ffffff">Fish & Chips + Drink = $15.00</text>
    </g>

    <!-- ELEVATOR FLOOR DISPLAY -->
    <g v-if="type === 'elevator-floor-display'">
      <rect x="10" y="10" width="180" height="130" rx="8" fill="#7f8c8d" stroke="#5d6d7e" stroke-width="4"/>
      <rect x="25" y="25" width="150" height="100" rx="4" fill="#0d1318"/>
      <text x="100" y="90" text-anchor="middle" font-family="monospace" font-size="60" font-weight="bold" fill="#e74c3c">12</text>
      <g transform="translate(155, 45)">
        <polygon points="0,15 10,0 20,15" fill="#27ae60"/>
      </g>
      <g transform="translate(155, 95)">
        <polygon points="0,0 10,15 20,0" fill="#34495e"/>
      </g>
      <text x="50" y="115" font-family="Arial" font-size="10" fill="#27ae60">▲ GOING UP</text>
    </g>

    <!-- QUEUE NUMBER -->
    <g v-if="type === 'queue-number'">
      <rect x="10" y="10" width="260" height="180" rx="8" fill="#2c3e50" stroke="#1a252f" stroke-width="4"/>
      <rect x="20" y="20" width="240" height="160" rx="4" fill="#0d1318"/>
      <text x="140" y="45" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#3498db">NOW SERVING</text>
      <text x="140" y="110" text-anchor="middle" font-family="monospace" font-size="56" font-weight="bold" fill="#f1c40f">A-047</text>
      <g transform="translate(140, 145)">
        <text x="0" y="0" text-anchor="middle" font-family="Arial" font-size="12" fill="#7f8c8d">COUNTER</text>
        <text x="0" y="20" text-anchor="middle" font-family="monospace" font-size="20" font-weight="bold" fill="#27ae60">3</text>
      </g>
      <g transform="translate(230, 35)">
        <path d="M0,0 L8,0 L15,-8 L15,8 L8,0" fill="#27ae60"/>
        <path d="M18,-5 Q22,0 18,5" fill="none" stroke="#27ae60" stroke-width="2"/>
        <path d="M21,-8 Q27,0 21,8" fill="none" stroke="#27ae60" stroke-width="2"/>
      </g>
    </g>

    <!-- SELF CHECKOUT -->
    <g v-if="type === 'self-checkout'">
      <rect x="10" y="10" width="300" height="200" rx="8" fill="#2c3e50" stroke="#1a252f" stroke-width="4"/>
      <rect x="20" y="20" width="280" height="130" rx="4" fill="#ffffff"/>
      <rect x="20" y="20" width="280" height="35" rx="4" fill="#27ae60"/>
      <text x="160" y="44" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#ffffff">SELF CHECKOUT</text>
      <g transform="translate(30, 65)">
        <text x="0" y="12" font-family="Arial" font-size="11" fill="#333">Milk 1L</text>
        <text x="200" y="12" font-family="Arial" font-size="11" fill="#333">$2.50</text>
        <text x="0" y="30" font-family="Arial" font-size="11" fill="#333">Bread</text>
        <text x="200" y="30" font-family="Arial" font-size="11" fill="#333">$1.80</text>
        <text x="0" y="48" font-family="Arial" font-size="11" fill="#333">Apples (3)</text>
        <text x="200" y="48" font-family="Arial" font-size="11" fill="#333">$3.20</text>
      </g>
      <line x1="30" y1="120" x2="290" y2="120" stroke="#bdc3c7" stroke-width="1"/>
      <text x="30" y="140" font-family="Arial" font-size="14" font-weight="bold" fill="#333">TOTAL:</text>
      <text x="230" y="140" font-family="Arial" font-size="18" font-weight="bold" fill="#27ae60">$7.50</text>
      <g transform="translate(20, 160)">
        <rect x="0" y="0" width="85" height="40" rx="4" fill="#e74c3c"/>
        <text x="42" y="25" text-anchor="middle" font-family="Arial" font-size="11" fill="#fff">CANCEL</text>
        <rect x="95" y="0" width="85" height="40" rx="4" fill="#f39c12"/>
        <text x="137" y="25" text-anchor="middle" font-family="Arial" font-size="11" fill="#fff">HELP</text>
        <rect x="190" y="0" width="90" height="40" rx="4" fill="#27ae60"/>
        <text x="235" y="25" text-anchor="middle" font-family="Arial" font-size="11" fill="#fff">PAY NOW</text>
      </g>
    </g>

    <!-- Label opcional -->
    <text
      v-if="label"
      x="160"
      y="235"
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
  width: { type: Number, default: 300 }, // Ancho base promedio aproximado
  type: { type: String, default: 'atm-insert-card' }, // Tipo por defecto
  label: { type: String, default: '' }
});

// Calculamos escala basada en el ancho deseado
// Usamos 300 como base estándar ya que la mayoría de dashboards son anchos
const scale = computed(() => {
  return props.width / 300;
});
</script>
