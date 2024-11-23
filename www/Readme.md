## Quick Reference:

 - To expand all child elements of the tree, hold down the Ctrl key while clicking on an item.
 - Plot discrete parameters in a separate chart.
 - If the CSV file doesn't include a date, the date and time will be relative to a default date. You can later shift the chart to the correct time.
 - Modern computers can easily display 1,000,000 data points thanks to WebGL. Ensure your data source isn't overloaded by such large queries.
 - Chart sizes can be adjusted. In the bottom right corner, there’s a standard resizing element, though it may be hard to notice.
 - Formulas use standard JS functions. The current value is substituted in place of *v*. Make sure to enclose expressions in parentheses when needed. For example, `0-v` won't work if *v* is less than zero. Use `0-(v)` instead.
 - Recalculation by formula or time shift does not trigger a new data request.
 - Multiple Y axes are NOT SUPPORTED!!!


## License

https://github.com/xabrs/trendviewer/

This program is free for both personal and commercial use and is licensed under the MIT License.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

This program uses the following libraries:

- **D3.js v3.5.16** - [https://d3js.org](https://d3js.org)
- **TWGL v4.21.2** - [https://twgljs.org](https://twgljs.org)
- **Vue.js v2.6.14** - [https://v2.vuejs.org](https://v2.vuejs.org)
- **Vuetify v2.7.2** - [https://v2.vuetifyjs.com](https://v2.vuetifyjs.com)
- **html2canvas 1.4.1** - <https://html2canvas.hertzen.com>