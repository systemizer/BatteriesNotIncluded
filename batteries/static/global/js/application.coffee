# Simple JavaScript Templating
# John Resig - http://ejohn.org/ - MIT Licensed
( ->
  cache = {}
  tmpl = @tmpl = (str, data) ->
    fn = new Function("obj", "var p=[],print=function(){p.push.apply(p,arguments);};with(obj){p.push('" +
      str.replace(/[\r\t\n]/g, " ")
        .split("<%").join("\t").replace(/((^|%>)[^\t]*)'/g, "$1\r")
        .replace(/\t=(.*?)%>/g, "',$1,'")
        .split("\t").join("');")
        .split("%>").join("p.push('")
        .split("\r").join("\\'") + "');}return p.join('');")
    if data
      fn(data)
    else
      fn
)()

find_templates = (elements) ->
  results = {}
  $(elements).each ->
    el = $(this)
    results[el.attr('id')] = tmpl(el.html())
  results

# find templates
templates = {}
$ -> window.templates = templates = find_templates('script[type="text/template"]')

# summarize
summarize = (elements, max_length) ->
  $(elements).each ->
    el = $(this)
    if el.text().length > max_length + 53
      el.data('full-text', el.text())
      el.text(el.text().substring(0, max_length) + '... ')
      el.append('<a href="#read-more" class="read-more">more</a>')
      el.find('.read-more').click(->
        el.text(el.data('full-text'))
        $(window).trigger('summary-expanded', [el, el.text()])
      )

$ -> summarize('.summarize', 250)

# masonry grid flow
$ ->
  elements = null
  resized = ->
    width = $(window).width()
    cutoff = 992
    if elements?
      elements.masonry('destroy')
      elements = null
    if width >= cutoff
      elements = $('.events')
      children = elements.find('.event')
      elements.masonry(
        itemSelector: '.event'
        columnWidth: children.width() + parseInt(children.css('padding-left'), 10) + parseInt(children.css('padding-right'), 10)
      )
  $(window).bind('resize', resized)
  $(window).bind('summary-expanded', resized)
  resized()
