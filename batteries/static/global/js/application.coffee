window.getCookie = getCookie = (name, source) ->
  source ?= document.cookie
  if source && source != ''
    cookies = source.split(';')
    for c in cookies
      [raw_name, value] = $.trim(c).split('=', 2)
      if raw_name == name
        return decodeURIComponent(value)
  return null

# modify ajax hook to send CSRF token for local requests
$(document).ajaxSend((evt, xhr, settings) ->
  sameOrigin = (url) ->
    host = document.location.host
    protocol = document.location.protocol
    sr_origin = '//' + host
    origin = protocol + sr_origin
    return (url == origin or url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        # or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url))

  safeMethod = (method) -> (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method))

  if not safeMethod(settings.type) && sameOrigin(settings.url)
    xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'))
)



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
  max_length ?= 150
  $(elements).each ->
    el = $(this)
    if el.text().length > max_length + 53
      return if el.data('full-text')?
      el.data('full-text', el.text())
      el.text(el.text().substring(0, max_length) + '... ')
      el.append('<a href="#read-more" class="read-more">more</a>')
      el.find('.read-more').click(->
        el.text(el.data('full-text'))
        $(window).trigger('summary-expanded', [el, el.text()])
      )

$ -> summarize('.summarize')

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


# provides python-like string formatting.
#
# >>> format('{{ 0 }} {{ 1 }}', 'hello', 'world')
# 'hello world'
# >>> format('{{ foo }} {{ bar }}', {foo: 'goodbye', bar: 'cruel world'})
# 'goodbye cruel world'
window.format = (string, values...) ->
  if (values.length < 1)
    return string
  # process like named argument (names pair up with object properties)
  if values.length == 1 && $.type(values[0]) == 'object'
    obj = values[0]
    string.replace(/{{ *([a-zA-Z0-9_-]+) *}}/g, (match, identifer) ->
      if obj[identifer]? then obj[identifer] else match
    )
  else
    # process as numbered arguments (names pair up with argument indices)
    string.replace(/{{ *(\d+) *}}/g, (match, index) ->
      if values[index]? then values[index] else match                                                                                                                                                 
    )

number_postfix = (n) ->
  if n == 1
    'st'
  else if n == 2
    'nd'
  else if n == 3
    'rd'
  else
    'th'

months = [
  'January', 'Feburary', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
  'November', 'October', 'December'
]

format_date = (str, date) ->
  format(str,
    year: date.getYear()
    month: months[date.getMonth()]
    day: date.getDay()
    day_th: number_postfix(date.getDay())
    hour: date.getHours() % 12 + 1
    min: date.getMinutes()
    apm: if date.getHours() < 12 then 'am' else 'pm'
  )

time_range = (start, end) ->
  diff = {
    year: start.getYear() != end.getYear()
    month: start.getMonth() != end.getMonth()
    day: start.getDay() != end.getDay()
    hour: start.getHours() != end.getHours()
    minute: start.getMinutes() != end.getMinutes()
    apm: (start.getHours() < 12) != (end.getHours() < 12)
  }
  str = []
  if diff.month
    str.push('{{ month }}')
  if diff.day
    if diff.year
      str.push('{{ day }}{{ day_th }},')
    else
      str.push('{{ day }}{{ day_th }}')
  if diff.year
    str.push('{{ year }}')
  if diff.hour or diff.minute
    if diff.minute
      str.push('{{ hour }}:{{ minute }}')
    else
      str.push('{{ hour }}')
  if diff.apm
    str.push('{{ apm }}')
  str = str.join(' ')
  result = format_date(str, start) + ' - ' + format_date(str, end)
  if not diff.apm
    result + format_date('{{ apm }}', end)
  else
    result

# templating from JSON
$ ->
  target = $('.events')
  get_events = (position) ->
    data = {}
    if position?
      data = {
        lat: position.coords.latitude
        lon: position.coords.longitude
      }
    $.ajax(
      url: '/api/events/'
      data: data
      type: 'get'
      dataType: 'json'
      success: (data) ->
        target.empty()
        for row in data.results
          start_time = new Date(row.start_time * 1000)
          end_time = new Date(row.end_time * 1000)
          target.append(templates.event_template(
            image_url: row.pic_square
            title: row.name
            time: time_range(start_time, end_time)
            location: row.location
            description: row.description
          ))
        summarize('.summarize')
      error: (req, stat, err) ->
        console.log(req, stat, err)
    )
  if navigator.geolocation?
    navigator.geolocation.getCurrentPosition(get_events, -> get_events())
  else
    get_events()

