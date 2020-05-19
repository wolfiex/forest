import {XYGlyph} from "models/glyphs/xy_glyph"
import {Text, TextView, TextData} from "models/glyphs/text"
import {TextVector} from "core/property_mixins"
//import {PointGeometry} from "core/geometry"
//import * as hittest from "core/hittest"
import {Arrayable} from "core/types"
import * as visuals from "core/visuals"
import * as p from "core/properties"
//import {measure_font} from "core/util/text"
//import {Context2d} from "core/util/canvas"
//import {assert} from "core/util/assert"
//import {Selection} from "../selections/selection"

export interface TextStampData extends TextData {
  _text: Arrayable<string>
  _angle: Arrayable<number>
  _x_offset: Arrayable<number>
  _y_offset: Arrayable<number>

  _sxs: number[][][]
  _sys: number[][][]
}

export interface TextStampView extends TextStampData {}

export class TextStampView extends TextView {
  model: TextStamp
  visuals: TextStamp.Visuals

}

export namespace TextStamp {
  export type Attrs = p.AttrsOf<Props>

  export type Props = XYGlyph.Props & {
    text: p.NullStringSpec
    angle: p.AngleSpec
    x_offset: p.NumberSpec
    y_offset: p.NumberSpec
  } & Mixins

  export type Mixins = TextVector

  export type Visuals = XYGlyph.Visuals & {text: visuals.Text}
}

export interface TextStamp extends TextStamp.Attrs {}

export class TextStamp extends Text {
  properties: TextStamp.Props
  __view_type__: TextStampView

  constructor(attrs?: Partial<TextStamp.Attrs>) {
    super(attrs)
  }

  static init_TextStamp(): void {
    this.prototype.default_view = TextStampView

  }
}
