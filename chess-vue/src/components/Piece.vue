<template>
  <div class="lattice">
    <div :class="classes" :style="style"></div>
    <div>
      <canvas
        v-if="isPoint([4, 1], [5, 2], [4, 8], [5, 9])"
        class="myCanvas"
      ></canvas>
      <div
        v-if="
          isPoint(
            [1, 2],
            [7, 2],
            [2, 3],
            [4, 3],
            [6, 3],
            [8, 3],
            [2, 6],
            [4, 6],
            [6, 6],
            [8, 6],
            [1, 7],
            [7, 7]
          )
        "
        class="chessItme chessItme1"
      ></div>
    </div>
    <div>
      <canvas
        v-if="isPoint([4, 1], [3, 2], [4, 8], [3, 9])"
        class="myCanvas2"
      ></canvas>
      <div
        v-if="
          isPoint(
            [1, 2],
            [7, 2],
            [2, 3],
            [4, 3],
            [6, 3],
            [0, 3],
            [2, 6],
            [4, 6],
            [6, 6],
            [0, 6],
            [1, 7],
            [7, 7]
          )
        "
        class="chessItme chessItme2"
      ></div>
    </div>
    <div>
      <canvas
        v-if="isPoint([5, 0], [4, 1], [5, 7], [4, 8])"
        class="myCanvas2"
      ></canvas>
      <div
        v-if="
          isPoint(
            [1, 2],
            [7, 2],
            [2, 3],
            [4, 3],
            [6, 3],
            [8, 3],
            [2, 6],
            [4, 6],
            [6, 6],
            [8, 6],
            [1, 7],
            [7, 7]
          )
        "
        class="chessItme chessItme3"
      ></div>
    </div>
    <div>
      <canvas
        v-if="isPoint([3, 0], [4, 1], [3, 7], [4, 8])"
        class="myCanvas"
      ></canvas>
      <div
        v-if="
          isPoint(
            [1, 2],
            [7, 2],
            [2, 3],
            [4, 3],
            [6, 3],
            [0, 3],
            [2, 6],
            [4, 6],
            [6, 6],
            [0, 6],
            [1, 7],
            [7, 7]
          )
        "
        class="chessItme chessItme4"
      ></div>
    </div>
  </div>
</template>

<script>
const IMG_MAP = {
  K: "/pieces/3.png",
  A: "/pieces/6.png",
  B: "/pieces/7.png",
  N: "/pieces/4.png",
  R: "/pieces/2.png",
  C: "/pieces/5.png",
  P: "/pieces/1.png",

  k: "/pieces/3-3.png",
  a: "/pieces/6-6.png",
  b: "/pieces/7-7.png",
  n: "/pieces/4-4.png",
  r: "/pieces/2-2.png",
  c: "/pieces/5-5.png",
  p: "/pieces/1-1.png",
};
export default {
  data() {
    return {};
  },
  props: ["board", "x", "y", "active", "targets", "lastMoveCoords"],
  computed: {
    piece() {
      let row = this.board[this.y];
      if (row) {
        let piece = row[this.x];
        if (piece) {
          return piece;
        }
      }
      return null;
    },
    classes() {
      let ret = ["chess"];
      if (this.isActive) {
        ret.push("chess-active");
      }
      return ret;
    },
    style() {
      let ret = {};
      let images = [];

      if (this.isTarget) {
        images.push(`url("/pieces/circle.png")`);
      }

      for (const coord of this.lastMoveCoords) {
        if (coord[0] === this.x && coord[1] === this.y) {
          images.push(`url("/pieces/move_indicator.svg")`);
        }
      }

      if (this.piece) {
        images.push(`url("${IMG_MAP[this.piece]}")`);
      }

      if (images.length > 0) {
        ret.backgroundImage = images.join(",");
      }

      return ret;
    },
    isActive() {
      return (
        this.active && this.active[0] == this.x && this.active[1] == this.y
      );
    },
    isTarget() {
      for (const target of this.targets) {
        if (target[0] == this.x && target[1] == this.y) {
          return true;
        }
      }
      return false;
    },
  },
  methods: {
    isPoint() {
      for (const point of arguments) {
        if (this.x === point[0] && this.y === point[1]) {
          return true;
        }
      }
      return false;
    },
  },
};
</script>
