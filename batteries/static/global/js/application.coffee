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

# escapes html, use for template tag
window.escapeHTML = (data) ->
  $(document.createElement('div')).html(data).text().replace('\n', '<br/>')

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
  max_length ?= 220
  $(elements).each ->
    el = $(this)
    if el.text().length > max_length + 53
      return if el.data('full-text')?
      el.data('full-text', el.text())
      el.text(el.text().substring(0, max_length) + '... ')
      el.append('<a href="#read-more" class="read-more">more</a>')
      el.find('.read-more').click ->
        el.text(el.data('full-text'))
        $(window).trigger('summary-expanded', [el, el.text()])
        return false

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
      # creating masonry temporarily removes the elements, losing the scroll position...
      sx = $(window).scrollTop()
      sy = $(window).scrollLeft()
      elements = $('.events')
      children = elements.find('.event')
      colWidth = children.width() +
          parseInt(children.css('padding-left'), 10) +
          parseInt(children.css('padding-right'), 10) +
          parseInt(children.css('margin-left'), 10) +
          parseInt(children.css('margin-right'), 10) +
          parseInt(children.css('border-left'), 10) +
          parseInt(children.css('border-right'), 10)
      elements.masonry(
        itemSelector: '.event'
        columnWidth: colWidth
      )
      $(window).scrollTop(sx)
      $(window).scrollLeft(sy)
  $(window).bind('resize', resized)
  $(window).bind('summary-expanded', resized)


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
  'January',
  'Feburary',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'November',
  'October',
  'December'
]

format_date = (str, date) ->
  hours = date.getHours() % 12
  if hours == 0
    hours = 12
  format(str,
    year: date.getFullYear()
    month: months[date.getMonth()].substring(0, 3)
    day: date.getDate()
    day_th: number_postfix(date.getDate())
    hour: hours
    minute: (if date.getMinutes() < 10 then '0' else '') + date.getMinutes()
    apm: if date.getHours() < 12 then 'am' else 'pm'
  )

date_range = (start, end) ->
  real_end = end?
  end ?= new Date()
  diff = {
    year: start.getFullYear() != end.getFullYear()
    month: start.getMonth() != end.getMonth()
    day: start.getDate() != end.getDate()
  }
  str = []
  if diff.month
    str.push('{{ month }}')
  if diff.day
    str.push('{{ day }}{{ day_th }}')
  if diff.year
    str[str.length - 1] = str[str.length - 1] + ','
    str.push('{{ year }}')
  str = str.join(' ')
  if str.length
    result = [format_date(str, start), format_date(str, end)]
  else
    result = [null, null]
  if diff.day and not diff.month
    if real_end
      result[0] = format_date('{{ month }} ', start) + result[0]
  if not real_end
    result[1] = null
  console.log('date_range', result, real_end)
  result

time_range = (start, end) ->
  real_end = end?
  console.log(real_end, end)
  end ?= new Date()
  diff = {
    hour: start.getHours() != end.getHours()
    minute: start.getMinutes() != end.getMinutes()
    apm: (start.getHours() <= 12) != (end.getHours() <= 12)
  }
  str = []
  if diff.hour or diff.minute
    if diff.minute
      str.push('{{ hour }}:{{ minute }}')
    else
      str.push('{{ hour }}')
  if diff.apm
    str[str.length - 1] = str[str.length - 1] + '{{ apm }}'
  str = str.join(' ')
  result = [format_date(str, start), format_date(str, end)]
  if not diff.apm
    if real_end
      result[1] += format_date('{{ apm }}', start)
    else
      result[0] += format_date('{{ apm }}', start)
  if not real_end
    result[1] = null
  console.log('time_range', result, real_end)
  result

time_until = (start, reference) ->
  reference ?= new Date()
  if (start.getFullYear() != reference.getFullYear() or start.getMonth() != reference.getMonth() or start.getDate() != reference.getDate())
    return ''
  diff = (start.getHours() * 60 + start.getMinutes()) - (reference.getHours() * 60 + reference.getMinutes())
  hours = Math.floor(diff / 60)
  minutes = diff % 60
  s = ''
  if hours > 0
    s = format('{{ 0 }} hour{{ 1 }}', hours, if hours == 1 then '' else 's')
  if minutes > 0
    if s != ''
      s += ', '
    s += format('{{ 0 }} minute{{ 1 }}', minutes, if minutes == 1 then '' else 's')
  s

null_empty_str = (s) -> if not s? or $.trim(s) == '' then null else s

# templating from JSON
$ ->
  target = $('.events')
  get_events = (position) ->
    data = {
      num_results: 20
      offset: 0
    }
    if position?
      $.extend(data, {
        lat: position.coords.latitude
        lon: position.coords.longitude
      })
    $.ajax(
      url: '/api/events/'
      data: data
      type: 'get'
      dataType: 'json'
      success: (data) ->
        target.empty()
        for row in data.results
          start_time = new Date(row.start_time * 1000 + 7200000)
          if row.end_time?
            end_time = new Date(row.end_time * 1000 + 7200000)
          else
            end_time = null
          console.log(row, row.start_time, start_time)
          results = date_range(start_time, end_time)
          date_start = results[0]
          date_end = results[1]
          results = time_range(start_time, end_time)
          time_start = results[0]
          time_end = results[1]
          timeuntil = time_until(start_time)

          results = row.location_gps.split(',')
          lat = parseFloat(results[0])
          lon = parseFloat(results[1])

          target.append(templates.event_template(
            h: escapeHTML
            has_coords: not isNaN(lat) and not isNaN(lon)
            lat: lat
            lon: lon
            url: row.url
            image_url: if row.pic_square? and $.trim(row.pic_square) != '' then row.pic_square else null
            title: row.name
            time_until: null_empty_str(timeuntil)
            start_date: null_empty_str(date_start)
            end_date: null_empty_str(date_end)
            start_time: null_empty_str(time_start)
            end_time: null_empty_str(time_end)
            location: row.location
            description: row.description
          ))
        summarize('.summarize')
        $(window).trigger('resize')
      error: (req, stat, err) ->
        console.error('no geolocation')
        console.log(req, stat, err)
    )
  if navigator.geolocation?
    navigator.geolocation.getCurrentPosition(get_events, -> get_events())
  else
    console.error('no geolocation')
    get_events()

