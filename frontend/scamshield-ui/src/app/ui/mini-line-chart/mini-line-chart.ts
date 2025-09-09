import { Component, Input, OnChanges, SimpleChanges, computed, signal } from '@angular/core';

@Component({
  selector: 'mini-line',
  standalone: true,
  template: `
<svg [attr.viewBox]="'0 0 ' + width + ' ' + height" style="width:100%;height:100px;">
<polyline [attr.points]="points()" fill="none" stroke="#6ad1ff" stroke-width="2" />
</svg>
`
})

export class MiniLineChart {
  @Input() values: number[] = [];
  width = 300; height = 80; pad = 6;
  private pts = signal('');
  points = computed(() => this.pts());


  ngOnChanges(_: SimpleChanges) {
    const { width, height, pad } = this;
    if (!this.values?.length) { this.pts.set(''); return; }
    const min = Math.min(...this.values);
    const max = Math.max(...this.values);
    const dx = (width - pad * 2) / (this.values.length - 1 || 1);
    const scaleY = (v: number) => max === min ? height / 2 : height - pad - ((v - min) / (max - min)) * (height - pad * 2);
    const pts = this.values.map((v, i) => `${pad + i * dx},${scaleY(v)}`).join(' ');
    this.pts.set(pts);
  }
}